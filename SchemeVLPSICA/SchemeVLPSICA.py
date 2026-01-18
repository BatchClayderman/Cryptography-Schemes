import os
from sys import argv, exit
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
from secrets import randbelow
from time import perf_counter, sleep
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element
except:
	print("The environment of the Python ``charm`` library is not handled correctly. ")
	print("See https://blog.csdn.net/weixin_45726033/article/details/144254189 in Chinese if necessary. ")
	print("Please press the enter key to exit. ")
	input()
	exit(-1)
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class SchemeVLPSICA:
	def __init__(self, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def __product(self:object, vec:tuple|list|set) -> Element:
		if isinstance(vec, (tuple, list, set)) and vec:
			element = vec[0]
			for ele in vec[1:]:
				element *= ele
			return element
		else:
			return self.__group.init(ZR, 1)
	def __computeLagrangeCoefficients(self:object, xPoints:tuple|list, yPoints:tuple|list, x:Element) -> Element:
		if (																																				\
			isinstance(xPoints, (tuple, list)) and isinstance(yPoints, (tuple, list)) and len(xPoints) == len(yPoints) and all(isinstance(ele, Element) and ele.type == ZR for ele in xPoints)		\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in yPoints) and isinstance(x, Element) and x.type == ZR													\
		):
			n, result = len(xPoints), self.__group.init(ZR, 1)
			for i in range(n):
				L_i = self.__group.init(ZR, 1)
				for j in range(n):
					if i != j:
						L_i *= (x - xPoints[j]) / (xPoints[i] - xPoints[j])
				result += yPoints[i] * L_i
			return result
		else:
			return self.__init(ZR, 0)
	def Setup(self:object, m:int = 10, n:int = 10, d:int = 10) -> tuple: # $\textbf{Setup}(m, n, d) \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		if isinstance(m, int) and m >= 1:
			self.__m = m
		else:
			self.__m = 10
			print("Setup: The variable $m$ should be a positive integer but it is not, which has been defaulted to $10$. ")
		if isinstance(n, int) and n >= 1:
			self.__n = n
		else:
			self.__n = 10
			print("Setup: The variable $n$ should be a positive integer but it is not, which has been defaulted to $10$. ")
		if isinstance(d, int) and d >= 1:
			self.__d = d
		else:
			self.__d = 10
			print("Setup: The variable $d$ should be a positive integer but it is not, which has been defaulted to $10$. ")
		
		# Scheme #
		g1 = self.__group.init(G1, 1) # $g_1 \gets 1_{\mathbb{G}_1}$
		g2 = self.__group.init(G2, 1) # $g_2 \gets 1_{\mathbb{G}_2}$
		s = self.__group.random(ZR) # generate $s \in \mathbb{Z}_p^*$ randomly
		SVec = tuple(g2 ** (s ** i) for i in range(self.__m + self.__d + 1)) # $\vec{S} \gets (S_0, S_1, \cdots, S_{m + d}) = (g_2^{s_0}, g_2^{s_1}, \cdots, g_2^{s^{m + d}})$
		SPrime = g1 ** s # $S' \gets g_1^s \in \mathbb{G}_1$
		if 512 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 384 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha384(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 256 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha256(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 224 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha224(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 160 == self.__group.secparam:
			H = lambda x:int.from_bytes(sha1(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 128 == self.__group.secparam:
			H = lambda x:int.from_bytes(md5(self.__group.serialize(x)).digest(), byteorder = "big")
		else:
			H = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest() * (((self.__group.secparam - 1) >> 9) + 1), byteorder = "big") & self.__operand # $H: \mathbb{G}_T \rightarrow \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
		self.__mpk = (g1, SPrime, H) # $\textit{mpk} \gets (g_1, S', H)$
		self.__msk = (g2, SVec) # $\textit{msk} \gets (g_2, \vec{S})$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def Sender(self:object, _vVec:tuple, _YVec:tuple) -> tuple: # $\textbf{Sender}(\vec{v}, \vec{Y}) \rightarrow (\vec{T} || \vec{T}', \vec{U} || \vec{U}')$
		# Check #
		if not self.__flag:
			print("Sender: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Sender`` subsequently. ")
			self.Setup()
		if isinstance(_vVec, tuple) and len(_vVec) == self.__d and all(isinstance(ele, Element) and ele.type == ZR for ele in _vVec): # hybrid check
			vVec = _vVec
		else:
			vVec = tuple(self.__group.random(ZR) for _ in range(self.__d))
			print("Sender: The variable $\\vec{v}$ should be a tuple containing $d$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(_YVec, tuple) and len(_YVec) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in _YVec): # hybrid check
			YVec = _YVec
		else:
			YVec = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Sender: The variable $\\vec{Y}$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g1, SPrime = self.__mpk[0], self.__mpk[1]
		
		# Scheme #
		k = randbelow(self.__n) # generate $k \in \mathbb{N}* \cap [0, n)$ randomly
		pi = lambda x:(x + k) % self.__n # $\pi: x \rightarrow (x + k) \% n$
		tVec = tuple(self.__group.random(ZR) for j in range(self.__n)) # generate $\vec{t} \gets (t_1, t_2, \cdots, t_n) \in \mathbb{Z}_r^n$ randomly
		TVec = tuple(g1 ** tVec[j] for j in range(self.__n)) # $\vec{T} \gets (T_1, T_2, \cdots, T_n) = (g_1^{t_1}, g_1^{t_2}, \cdots, g_1^{t_n})$
		UVec = tuple(SPrime * g1 ** (-YVec[pi(j)]) for j in range(self.__n)) # $\vec{U} \gets (U_1, U_2, \cdots, U_n) = (S' \cdot (g_1^{-y_{\pi(1)}}), S' \cdot (g_1^{-y_{\pi(2)}}), \cdots, S' \cdot (g_1^{-y_{\pi(n)}}))$
		tPrimeVec = tuple(self.__group.random(ZR) for _ in range(self.__d)) # generate $\vec{t}' = (t'_1, t'_2, \cdots, t'_d) \in \mathbb{Z}_r^d$ randomly
		TPrimeVec = tuple(g1 ** tPrimeVec[j] for j in range(self.__d)) # $\vec{T}' \gets (T'_1, T'_2, \cdots, T'_d) = (g_1^{t'_1}, g_1^{t'_2}, \cdots, g_1^{t'_d})$
		UPrimeVec = tuple(SPrime * g1 ** (-vVec[j]) ** tPrimeVec[j] for j in range(self.__d)) # $\vec{U}' \gets (U'_1, U'_2, \cdots, U'_d) = (S' \cdot (g_1^{-v_1})^{t'_1}, S' \cdot (g_1^{-v_2})^{t'_2}, \cdots, S' \cdot (g_1^{-v_d})^{t'_d})$
		
		# Return #
		return (TVec + TPrimeVec, UVec + UPrimeVec) # \textbf{return} $(\vec{T} || \vec{T}', \vec{U} || \vec{U}')$
	def Receiver(self:object, _vVec:tuple, _XVec:tuple) -> tuple: # $\textbf{Receiver}(\vec{v}, \vec{X}) \rightarrow (R, \vec{R}')$
		# Check #
		if not self.__flag:
			print("Receiver: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Receiver`` subsequently. ")
			self.Setup()
		if isinstance(_vVec, tuple) and len(_vVec) == self.__d and all(isinstance(ele, Element) and ele.type == ZR for ele in _vVec): # hybrid check
			vVec = _vVec
		else:
			vVec = tuple(self.__group.random(ZR) for _ in range(self.__d))
			print("Receiver: The variable $\\vec{v}$ should be a tuple containing $d$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(_XVec, tuple) and len(_XVec) == self.__m and all(isinstance(ele, Element) and ele.type == ZR for ele in _XVec): # hybrid check
			XVec = _XVec
		else:
			XVec = tuple(self.__group.random(ZR) for _ in range(self.__m))
			print("Receiver: The variable $\\vec{X}$ should be a tuple containing $m$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		SVec = self.__msk[1]
		
		# Scheme #
		XPrimeVec = XVec + vVec # $\vec{X}' \gets (\vec{X} || \vec{v}) \in \mathbb{Z}_r^{m + d}$
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_r$ randomly
		xPoints, yPoints = tuple(self.__group.init(ZR, j) for j in range(1, self.__m + self.__d + 1)), XPrimeVec
		R = self.__product(tuple(SVec[j] ** self.__computeLagrangeCoefficients(xPoints, yPoints, self.__group.init(ZR, j)) for j in range(self.__m + self.__d + 1))) ** r # $R \gets \left(\prod\limits_{j = 0}^{m + d} S_j^{p(X', j)}\right)^r$
		RPrimeVec = tuple(
			self.__product(tuple(SVec[j] ** self.__computeLagrangeCoefficients(xPoints, yPoints, self.__group.init(ZR, j)) for j in range(self.__m + self.__d))) ** r for i in range(self.__m + self.__d)
		) # $R_{-i} \gets \left(\prod\limits_{j = 0}^{m + d - 1} S_j^{p(X'_{-i}, j)}\right)^r, \forall i \in {1, 2, \cdots, m + d}$
		del xPoints, yPoints
		
		# Return #
		return (R, RPrimeVec) # \textbf{return} $(R, \vec{R}')$
	def Cloud1(self:object, _TTPrime:tuple, _R:Element) -> tuple: # $\textbf{Cloud1}((\vec{T}, \vec{T}'), R) \rightarrow \vec{W}$
		# Check #
		if not self.__flag:
			print("Cloud1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Cloud1`` subsequently. ")
			self.Setup()
		if isinstance(_TTPrime, tuple) and len(_TTPrime) == self.__n + self.__d and all(isinstance(ele, Element) and ele.type == G1 for ele in _TTPrime): # hybrid check
			TTPrime = _TTPrime
		else:
			TTPrime = tuple(self.__group.random(G1) for _ in range(self.__n + self.__d))
			print("Cloud1: The variable $\\vec{{T}} || \\vec{{T}}'$ should be a tuple containing $n + d = {0} + {1} = {2}$ elements of $\\mathbb{{G}}_1$ but it is not, which has been generated randomly. ".format(self.__n, self.__d, self.__n + self.__d))
		if isinstance(_R, Element) and _R.type == G2: # type check
			R = _R
		else:
			R = self.__group.random(G2)
			print("Cloud1: The variable $R$ should be an element of $\\mathbb{G}_2$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		H = self.__mpk[2]
		
		# Scheme #
		WVec = tuple(H(pair(TTPrime[j], R)) for j in range(self.__n + self.__d)) # $W_j \gets H(e((\vec{T} || \vec{T}')_j, R)), \forall j \in {1, 2, \cdots, n + d}$
		k1 = randbelow(self.__n + self.__d) # generate $k_1 \in \mathbb{N}* \cap [0, n + d)$ randomly
		pi1 = lambda x:(x + k1) % (self.__n + self.__d) # $\pi_1: x \rightarrow (x + k_1) \% (n + d)$
		WVec = tuple(WVec[pi1(j)] for j in range(self.__n + self.__d)) # $\vec{W} \gets \{\vec{W}_{\pi_1(j)}\}_j$
		
		# Return #
		return WVec # \textbf{return} $\vec{W}$
	def Cloud2(self:object, _UUPrime:tuple, _RPrimeVec:tuple) -> tuple: # $\textbf{Cloud2}(\vec{U}, R') \rightarrow \vec{K}$
		# Check #
		if not self.__flag:
			print("Cloud2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Cloud2`` subsequently. ")
			self.Setup()
		if isinstance(_UUPrime, tuple) and len(_UUPrime) == self.__n + self.__d and all(isinstance(ele, Element) and ele.type == G1 for ele in _UUPrime): # hybrid check
			UUPrime = _UUPrime
		else:
			UUPrime = tuple(self.__group.random(G1) for _ in range(self.__n + self.__d))
			print("Cloud2: The variable $\\vec{{U}} || \\vec{{U}}'$ should be a tuple containing $n + d = {0} + {1} = {2}$ elements of $\\mathbb{{G}}_1$ but it is not, which has been generated randomly. ".format(self.__n, self.__d, self.__n + self.__d))
		if isinstance(_RPrimeVec, tuple) and len(_RPrimeVec) == self.__m + self.__d and all(isinstance(ele, Element) and ele.type == G2 for ele in _RPrimeVec): # hybrid check
			RPrimeVec = _RPrimeVec
		else:
			RPrimeVec = tuple(self.__group.random(G2) for _ in range(self.__m + self.__d))
			print("Cloud2: The variable $\\vec{{R}}'$ should be a tuple containing $m + d = {0} + {1} = {2}$ elements of $\\mathbb{{G}}_1$ but it is not, which has been generated randomly. ".format(self.__m, self.__d, self.__m + self.__d))
		
		# Unpack #
		H = self.__mpk[2]
		
		# Scheme #
		KVec = tuple(H(pair(UUPrime[j], RPrimeVec[i])) for i in range(self.__m + self.__d) for j in range(self.__n + self.__d)) # $\vec{K}_{i(n + d) + j} \gets H(e((\vec{U} || \vec{U}')_j, R'_i)), \forall i \in {1, 2, \cdots, m + d}, \forall j \in {1, 2, \cdots, n + d}$
		k2 = randbelow((self.__m + self.__d) * (self.__n + self.__d)) # generate $k_2 \in \mathbb{N}* \cap [0, (m + d)(n + d))$ randomly
		pi2 = lambda i, j:(i * (self.__n + self.__d) + j + k2) % ((self.__m + self.__d) * (self.__n + self.__d)) # $\pi_2: i, j \rightarrow (i(n + d) + j + k_2) \% (m + d)(n + d)$
		KVec = tuple(KVec[pi2(i, j)] for i in range(self.__m + self.__d) for j in range(self.__n + self.__d)) # $\vec{K} \gets \{\vec{K}_{\pi_2(i, j)}\}_{i, j}$
		
		# Return #
		return KVec # \textbf{return} $\vec{K}$
	def Verify(self:object, _KVec:tuple, _WVec:tuple) -> int|bool: # $\textbf{Verify}(\vec{K}, \vec{W}) \rightarrow \textit{result}$
		# Check #
		if not self.__flag:
			print("Verify: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Verify`` subsequently. ")
			self.Setup()
		if isinstance(_KVec, tuple) and len(_KVec) == (self.__m + self.__d) * (self.__n + self.__d) and all(isinstance(ele, int) for ele in _KVec): # hybrid check
			KVec = _KVec
		else:
			KVec = self.Cloud2(tuple(self.__group.random(G1) for _ in range(self.__n + self.__d)), tuple(self.__group.random(G2) for _ in range(self.__m + self.__d)))
			print("Verify: The variable $\\vec{{K}}$ should be a tuple containing $(m + d)(n + d) = {0}$ integers but it is not, which has been generated randomly. ".format((self.__m + self.__d) * (self.__n + self.__d)))
		if isinstance(_WVec, tuple) and len(_WVec) == self.__n + self.__d and all(isinstance(ele, int) for ele in _WVec): # hybrid check
			WVec = _WVec
		else:
			WVec = self.Cloud1(tuple(self.__group.random(G1) for _ in range(self.__n + self.__d)), self.__group.random(G2))
			print("Verify: The variable $\\vec{{W}}$ should be a tuple containing $n + d = {0} + {1} = {2}$ integers but it is not, which has been generated randomly. ".format(self.__n, self.__d, self.__n + self.__d))
		
		# Unpack #
		pass
		
		# Scheme #
		if set(WVec) <= set(KVec): # \textbf{if} $\vec{W} \subseteq \vec{K}$ \textbf{then}
			result = self.__n # \quad$\textit{result} \gets |\vec{K} \cap \vec{W}| - d = |\vec{W}| - d = n + d - d = n$
		else: # \textbf{else}
			result = False # \quad$\textit{result} \gets \perp$
		# \textbf{end if}
		
		# Return #
		return result # \textbf{return} $\textit{result}$
	def getLengthOf(self:object, obj:Element|tuple|list|set|bytes|int) -> int:
		if isinstance(obj, Element):
			return len(self.__group.serialize(obj))
		elif isinstance(obj, (tuple, list, set)):
			sizes = tuple(self.getLengthOf(o) for o in obj)
			return -1 if -1 in sizes else sum(sizes)
		elif isinstance(obj, bytes):
			return len(obj)
		elif isinstance(obj, int) or callable(obj):
			return self.__group.secparam >> 3
		else:
			return -1


def Scheme(curveType:tuple|list|str, m:int = 10, n:int = 10, d:int = 10, round:int|None = None) -> list:
	# Begin #
	if isinstance(m, int) and isinstance(n, int) and isinstance(d, int) and m >= 1 and n >= 1 and d >= 1:
		try:
			if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
				if curveType[1] >= 1:
					group = PairingGroup(curveType[0], secparam = curveType[1])
				else:
					group = PairingGroup(curveType[0])
			else:
				group = PairingGroup(curveType)
		except BaseException as e:
			if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
				print("curveType =", curveType[0])
				if curveType[1] >= 1:
					print("secparam =", curveType[1])
			elif isinstance(curveType, str):
				print("curveType =", curveType)
			else:
				print("curveType = Unknown")
			print("m =", m)
			print("n =", n)
			print("d =", d)
			if isinstance(round, int) and round >= 0:
				print("round =", round)
			print("Is the system valid? No. \n\t{0}".format(e))
			return (																																														\
				([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [(curveType if isinstance(curveType, str) else None), None])		\
				+ [m, n, d, round if isinstance(round, int) and round >= 0 else None] + [False] * 3 + [-1] * 19																												\
			)
	else:
		print("Is the system valid? No. The parameters $m$, $n$, and $d$ should be three positive integers. ")
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [(curveType if isinstance(curveType, str) else None), None])		\
			+ [m if isinstance(m, int) else None, n if isinstance(n, int) else None, d if isinstance(d, int) else None, round if isinstance(round, int) and round >= 0 else None] + [False] * 3 + [-1] * 19											\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	print("m =", m)
	print("n =", n)
	print("d =", d)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeVLPSICA = SchemeVLPSICA(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeVLPSICA.Setup(m, n, d)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Sender #
	startTime = perf_counter()
	vVec = tuple(group.random(ZR) for _ in range(d))
	YVec = tuple(group.random(ZR) for _ in range(n))
	TTPrime, UUPrime = schemeVLPSICA.Sender(vVec, YVec)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Receiver #
	startTime = perf_counter()
	XVec = tuple(group.random(ZR) for _ in range(m))
	R, RPrimeVec = schemeVLPSICA.Receiver(vVec, XVec)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Cloud1 #
	startTime = perf_counter()
	WVec = schemeVLPSICA.Cloud1(TTPrime, R)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Cloud2 #
	startTime = perf_counter()
	KVec = schemeVLPSICA.Cloud2(UUPrime, RPrimeVec)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Verify #
	startTime = perf_counter()
	result = schemeVLPSICA.Verify(KVec, WVec)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, isinstance(result, int)]
	spaceRecords = [																																									\
		schemeVLPSICA.getLengthOf(group.random(ZR)), schemeVLPSICA.getLengthOf(group.random(G1)), schemeVLPSICA.getLengthOf(group.random(G2)), schemeVLPSICA.getLengthOf(group.random(GT)), 	\
		schemeVLPSICA.getLengthOf(mpk), schemeVLPSICA.getLengthOf(msk), schemeVLPSICA.getLengthOf(TTPrime), schemeVLPSICA.getLengthOf(UUPrime), schemeVLPSICA.getLengthOf(R), 				\
		schemeVLPSICA.getLengthOf(RPrimeVec), schemeVLPSICA.getLengthOf(WVec), schemeVLPSICA.getLengthOf(KVec)																			\
	]
	del schemeVLPSICA
	print("Verify:", result)
	print("Is the scheme passed (result != False)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, m, n, d, round if isinstance(round, int) else None] + booleans + timeRecords + spaceRecords

def parseCL(vec:list) -> tuple:
	owOption, sleepingTime = 0, None
	for arg in vec:
		if isinstance(arg, str):
			if arg.upper() in ("Y", "YES", "TRUE"):
				owOption = 2
			elif arg.upper() in ("N", "NO", "FALSE"):
				owOption = 1
			elif arg.upper() in ("C", "CANCEL"):
				owOption = -1
			elif arg.upper() in ("Q", "QUESTION", "A", "ASK", "NONE"):
				owOption = 0
			else:
				try:
					sleepingTime = float(arg)
				except:
					pass
	return (owOption, sleepingTime)

def handleFolder(fd:str) -> bool:
	folder = str(fd)
	if not folder:
		return True
	elif os.path.exists(folder):
		return os.path.isdir(folder)
	else:
		try:
			os.makedirs(folder)
			return True
		except:
			return False

def main() -> int:
	# Begin #
	curveTypes = ("MNT159", "MNT201", "MNT224", "BN254", ("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
	roundCount, filePath = 100, "SchemeVLPSICA.xlsx"
	queries = ["curveType", "secparam", "m", "n", "d", "roundCount"]
	validators = ["isSystemValid", "isSchemePassed"]
	metrics = 	[																	\
		"Setup (s)", "Sender (s)", "Receiver (s)", "Cloud1 (s)", "Cloud 2(s)", "Verify (s)",		\
		"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 		\
		"mpk (B)", "msk (B)", "(T, T') (B)", "(U, U') (B)", "R (B)", "R' (B)", "W (B)", "K (B)"	\
	]
	
	# Scheme #
	qLength, columns, results = len(queries), queries + validators + metrics, []
	length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
	try:
		for curveType in curveTypes:
			for m in range(5, 31, 5):
				for n in range(5, 31, 5):
					for d in range(5, 31, 5):
						average = Scheme(curveType, m = m, n = n, d = d, round = 0)
						for round in range(1, roundCount):
							result = Scheme(curveType, m = m, n = n, d = d, round = round)
							for idx in range(qLength, qvLength):
								average[idx] += result[idx]
							for idx in range(qvLength, length):
								average[idx] = -1 if average[idx] < 0 or result[idx] < 0 else average[idx] + result[idx]
						average[avgIndex] = roundCount
						for idx in range(qvLength, length):
							average[idx] = -1 if average[idx] <= 0 else average[idx] / roundCount
						results.append(average)
	except KeyboardInterrupt:
		print("\nThe experiments were interrupted by users. The program will try to save the results collected. ")
	except BaseException as e:
		print("The experiments were interrupted by the following exceptions. The program will try to save the results collected. \n\t{0}".format(e))
	
	# Output #
	owOption, sleepingTime = parseCL(argv[1:])
	print()
	if results:
		if -1 == owOption:
			print("Results: \n{0}\n".format(results))
		elif handleFolder(os.path.split(filePath)[0]):
			# Writing Preparation #
			if os.path.isfile(filePath):
				if 1 == owOption:
					flag = False # write to the file or not
				elif 2 == owOption:
					flag = True
				else:
					try:
						flag = input("The file \"{0}\" exists. Overwrite the file or not [yN]? ".format(filePath)).upper() in ("Y", "YES", "TRUE", "1")
					except:
						flag = False
						print()
			else:
				flag = True
			
			# Writing Handling #
			if flag:
				try:
					df = __import__("pandas").DataFrame(results, columns = columns)
					if os.path.splitext(filePath)[1].lower() == ".csv":
						df.to_csv(filePath, index = False, float_format = "%.9f")
					else:
						df.to_excel(filePath, index = False, float_format = "%.9f")
					print("Successfully saved the results to \"{0}\" in the three-line table form. ".format(filePath))
				except:
					try:
						with open(filePath, "w", encoding = "utf-8") as f:
							f.write(str(columns) + "\n" + str(results))
						print("Successfully saved the results to \"{0}\" in the plain text form. ".format(filePath))
					except BaseException as e:
						print("Results: \n{0}\n\nFailed to save the results to \"{1}\" due to the following exception(s). \n\t{2}".format(results, filePath, e))
			else:
				print("Results: \n{0}\n\nThe overwriting is canceled by users. ".format(results))
		else:
			print("Results: \n{0}\n\nFailed to save the results to \"{1}\" since the parent folder was not created successfully. ".format(results, filePath))
	else:
		print("The results are empty. ")
	
	# End #
	errorLevel = EXIT_SUCCESS if results and all([all([r == roundCount for r in result[5:8]] + [r > 0 for r in result[8:length]]) for result in results]) else EXIT_FAILURE
	try:
		if isinstance(sleepingTime, float) and 0 <= sleepingTime < float("inf"):
			print("Please wait for the countdown ({0} second(s)) to end, or exit the program manually like pressing the \"Ctrl + C\" ({1}). \n".format(sleepingTime, errorLevel))
			sleep(sleepingTime)
		else:
			print("Please press the enter key to exit ({0}). ".format(errorLevel))
			input()
	except:
		print()
	return errorLevel



if "__main__" == __name__:
	exit(main())