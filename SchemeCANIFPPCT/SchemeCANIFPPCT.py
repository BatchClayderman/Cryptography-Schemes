import os
from sys import argv, exit
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


class SchemeCANIFPPCT:
	def __init__(self, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__n = 30
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
	def Setup(self:object, n:int = 30) -> tuple: # $\textbf{Setup}(n) \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		if isinstance(n, int) and n >= 1:
			self.__n = n
		else:
			self.__n = 30
			print("Setup: The variable $n$ should be a positive integer but it is not, which has been defaulted to $30$. ")
		
		# Scheme #
		p = self.__group.order() # $p \gets \|\mathbb{G}\|$
		g1 = self.__group.init(G1, 1) # $g_1 \gets 1_{\mathbb{G}_1}$
		g2 = self.__group.init(G2, 1) # $g_2 \gets 1_{\mathbb{G}_2}$
		g3 = self.__group.random(G1) # generate $g_3 \in \mathbb{G}_1$ randomly
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(self.__group.serialize(x), ZR) # $H_2: \mathbb{G}_T \rightarrow \mathbb{Z}_r$
		H3 = lambda x:self.__group.hash(x, ZR) # $H_3: \{0, 1\}^* \rightarrow \mathbb{Z}_r$
		H4 = lambda x:self.__group.hash(self.__group.serialize(x), ZR) # $H_4: \mathbb{G}_1 \rightarrow \mathbb{Z}_r$
		r, s, t, omega, t1, t2, t3, t4 = self.__group.random(ZR, 8) # generate $r, s, t, \omega, t_1, t_2, t_3, t_4 \in \mathbb{Z}_r$ randomly
		R = g1 ** r # $R \gets g_1^r$
		S = g2 ** s # $S \gets g_2^s$
		T = g1 ** t # $T \gets g_1^t$
		Omega = pair(g1, g2) ** (t1 * t2 * omega) # $\Omega \gets e(g_1, g_2)^{t_1 t_2 \omega}$
		v1 = g2 ** t1 # $v_1 \gets g_2^{t_1}$
		v2 = g2 ** t2 # $v_2 \gets g_2^{t_2}$
		v3 = g2 ** t3 # $v_3 \gets g_2^{t_3}$
		v4 = g2 ** t4 # $v_4 \gets g_2^{t_4}$
		self.__mpk = (g1, g2, p, g3, H1, H2, H3, H4, R, S, T, Omega, v1, v2, v3, v4) # $ \textit{mpk} \gets (g_1, g_2, p, g_3, H_1, H_2, H_3, H_4, R, S, T, \Omega, v_1, v_2, v_3, v_4)$
		self.__msk = (r, s, t, omega, t1, t2, t3, t4) # $\textit{msk} \gets (r, s, t, \omega, t_1, t_2, t_3, t_4)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def KGen(self:object, IDi:tuple) -> tuple: # $\textbf{KGen}(\textit{ID}_i) \rightarrow (\textit{sk}_{\textit{ID}_i}, \textit{ek}_{\textit{ID}_i})$
		# Check #
		if not self.__flag:
			print("KGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``KGen`` subsequently. ")
			self.Setup()
		if isinstance(IDi, tuple) and 2 <= len(IDk) < self.__l and all([isinstance(ele, Element) and ele.type == ZR for ele in IDk]): # hybrid check
			ID_k = IDk
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																					\
				(																																					\
					"KGen: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $k \\in [2, {0}]$ but it is not, "	\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																						\
				).format(self.__l - 1, self.__l)																																\
			)
		
		# Unpack #
		g1 = self.__mpk[0]
		
		# Scheme #
		k_i, x_i = self.__group.random(ZR), self.__group.random(ZR) # generate $k_i, x_i \in \mathbb{Z}_r$ randomly
		z_i = (r - x_i) * (s * x_i) ** (-1) # $z_i \gets (r - x_i)(s x_i)^{-1} \in \mathbb{Z}_r$
		Z_i = g1 ** z_i # $Z_i \gets g_1^{z_i} \in \mathbb{G}_1$
		sk_ID_i = k_i # $\textit{sk}_{\textit{ID}_i} \gets k_i$
		ek_ID_i = (x_i, Z_i) # $\textit{ek}_{\textit{ID}_i} \gets (x_i, Z_i)$
		tag_i = H4(x_i * Z_i) # $\textit{tag}_i \gets H_4(x_i \cdot Z_i)$
		
		# Return #
		return (sk_ID_i, ek_ID_i) # \textbf{return} $(\textit{sk}_{\textit{ID}_i}, \textit{ek}_{\textit{ID}_i}$
	def Encryption(self:object, TPS:tuple, ekIDi:Element) -> object: # $\textbf{Encryption}(\textit{TP}_S, \textit{ek}_{\textit{ID}_i}) \rightarrow \textit{CT}_{\textit{TP}_S})$
		# Check #
		if not self.__flag:
			print("Encryption: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Encryption`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l and all([isinstance(ele, Element) and ele.type == ZR for ele in IDk]): # hybrid check
			ID_k = IDk
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																						\
				(																																						\
					"Encryption: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $k \\in [2, {0}]$ but it is not, "		\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																							\
				).format(self.__l - 1, self.__l)																																	\
			)
		if isinstance(message, Element) and message.type == GT: # type check
			M = message
		else:
			M = self.__group.random(GT)
			print("Encryption: The variable $M$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g1, g2, g3, gBar, gTilde, h = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[8:]
		k = len(ID_k)
		
		# Scheme #
		sVec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{s} = (s_1, s_2, \cdots, s_n) \in \mathbb{Z}_r^n$ randomly
		s1Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{s}_1 = (s_{1_1}, s_{1_2}, \cdots, s_{1, n}) \in mathbb{Z}_r^n$ randomly
		s2Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{s}_2 = (s_{2_1}, s_{2_2}, \cdots, s_{2, n}) \in mathbb{Z}_r^n$ randomly
		V = tuple(H2(Omega ** s[i]) for i in range(self.__n)) # $V_i \gets H_2(\Omega^{s_i}), \forall i \in \{1, 2, \cdots, n\}$
		C0Vec = tuple((g3 * H1(TP_S[i])) ** s[i] for i in range(self.__n)) # $\vec{C}_{i, 0} \gets (g_3 H_1(\textit{TP}_S))^{s_i}, \forall i \in \{1, 2, \cdots, n\}$
		C1Vec = tuple(v1 ** (s[i] - s1[i]) for i in range(self.__n)) # $\vec{C}_{i, 1} \gets v_1^{s_i - s_{i, 1}}$
		C2Vec = tuple(v2 ** s1[i] for i in range(self.__n)) # $\vec{C}_{i, 2} \gets v_2^{s_{i, 1}}$
		C3Vec = tuple(v3 ** (s[i] - s2[i]) for i in range(self.__n)) # $\vec{C}_{i, 3} \gets v_3^{s_i - s_{i, 2}}$
		C4Vec = tuple(v4 ** s2[i] for i in range(self.__n)) # $\vec{C}_{i, 4} \gets v_4^{s_{i, 2}}$
		f = lambda x:self.__product(x - V[i] for i in range(self.__n)) # $f(x) := \prod\limits_{i = 1}^n (x - V_i)$
		alpha = self.__group.random(ZR) # generate $\alpha \in \mathbb{Z}_r$ randomly
		C1 = g1 ** alpha # $C_1 \gets g_1^\alpha$
		C2 = Zi ** xi + T ** alpha # $C_2 \gets Z_i^{x_i} + T^\alpha$
		C3 = pair(T, S) ** alpha # $C_3 \gets e(T, S)^\alpha$
		C4 = H3()
		C5 = kc + x_i
		
		# Return #
		return CT # $\textbf{return }\textit{CT}$
	def DerivedKGen(self:object, skIDkMinus1:tuple, IDk:tuple) -> tuple: # $\textbf{DerivedKGen}(\textit{sk}_{\textit{ID}_\textit{k - 1}}, \textit{ID}_k) \rightarrow \textit{sk}_{\textit{ID}_k}$
		# Check #
		if not self.__flag:
			print("DerivedKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DerivedKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l and all([isinstance(ele, Element) and ele.type == ZR for ele in IDk]): # hybrid check
			ID_k = IDk
			if isinstance(skIDkMinus1, tuple) and len(skIDkMinus1) == ((self.__l - len(ID_k) + 1) << 2) + 5 and all([isinstance(ele, Element) for ele in skIDkMinus1]): # hybrid check
				sk_ID_kMinus1 = skIDkMinus1
			else:
				sk_ID_kMinus1 = self.KGen(ID_k[:-1])
				print(
					(
						"DerivedKGen: The variable $\\textit{{sk}}_{{\\textit{{ID}}_{{k - 1}}}}$ should be a tuple containing $(l - k + 1) \\times 4 + 5 = {0}$ elements but it is not, "
						+ "which has been generated accordingly. "
					).format(((self.__l - len(ID_k) + 1) << 2) + 5)
				)
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																								\
				(																																								\
					"DerivedKGen: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements of $\\mathbb{{Z}}_r$ where the integer $k \\in [2, {0}]$ but it is not, "		\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																									\
				).format(self.__l - 1, self.__l)																																			\
			)
			sk_ID_kMinus1 = self.KGen(ID_k[:-1])
			print("DerivedKGen: The variable $\\textit{sk}_{\\textit{ID}_{k - 1}}$ has been generated accordingly. ")
		
		# Unpack #
		g, g3Bar, g3Tilde, h = self.__mpk[0], self.__mpk[6], self.__mpk[7], self.__mpk[8:]
		k = len(ID_k)
		a0, a1, b, f0, f1 = sk_ID_kMinus1[0], sk_ID_kMinus1[1], sk_ID_kMinus1[2], sk_ID_kMinus1[-2], sk_ID_kMinus1[-1] # first 3 and last 2
		lengthPerToken = self.__l - k + 1
		c0, c1, d0, d1 = sk_ID_kMinus1[3:3 + lengthPerToken], sk_ID_kMinus1[3 + lengthPerToken:3 + (lengthPerToken << 1)], sk_ID_kMinus1[-2 - (lengthPerToken << 1):-2 - lengthPerToken], sk_ID_kMinus1[-2 - lengthPerToken:-2]
		
		# Scheme #
		t = self.__group.random(ZR) # generate $t \in \mathbb{Z}_r$ randomly
		sk_ID_k = ( # $\textit{sk}_{\textit{ID}_k} \gets (
			(
				a0 * c0[0] ** ID_k[k - 1] * (f0 * d0[0] ** ID_k[k - 1] * g3Bar) ** t, # a_0 \cdot c_{0, k}^{I_k} \cdot (f_0 \cdot d_{0, k}^{I_k} \cdot \bar{g}_3)^t, 
				a1 * c1[0] ** ID_k[k - 1] * (f1 * d1[0] ** ID_k[k - 1] * g3Tilde) ** t, # a_1 \cdot c_{1, k}^{I_k} \cdot (f_1 \cdot d_{1, k}^{I_k} \cdot \tilde{g}_3)^t, 
				b * g ** t, # b \cdot g^t, 
			)
			+ tuple(c0[i] * d0[i] ** t for i in range(1, lengthPerToken)) # c_{0, k + 1} \cdot d_{0, k + 1}^t, c_{0, k + 2} \cdot d_{0, k + 2}^t, \cdots, c_{0, l} \cdot d_{0, l}^t, 
			+ tuple(c1[i] * d1[i] ** t for i in range(1, lengthPerToken)) # c_{1, k + 1} \cdot d_{1, k + 1}^t, c_{1, k + 2} \cdot d_{1, k + 2}^t, \cdots, c_{1, l} \cdot d_{1, l}^t, 
			+ tuple(d0[i] for i in range(1, lengthPerToken)) # d_{0, k + 1}, d_{0, k + 2}, \cdots, d_{0, l}, 
			+ tuple(d1[i] for i in range(1, lengthPerToken)) # d_{1, k + 1}, d_{1, k + 2}, \cdots, d_{1, l}, 
			+ (f0 * c0[0] ** ID_k[k - 1], f1 * c1[0] ** ID_k[k - 1]) # f_0 \cdot c_{0, k}^{I_k}, f_1 \cdot c_{1, k}^{I_k}
		) # )$
		
		# Return #
		return sk_ID_k # $\textbf{return }\textit{sk}_{\textit{ID}_k}$
	def Dec(self:object, skIDk:tuple, cipherText:tuple) -> bytes: # $\textbf{Dec}(\textit{sk}_{\textit{ID}_k}, \textit{CT}) \rightarrow M$
		# Check #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if isinstance(skIDk, tuple) and 9 <= len(skIDk) <= ((self.__l - 1) << 2) + 5 and all([isinstance(ele, Element) for ele in skIDk]): # hybrid check
			sk_ID_k = skIDk
		else:
			sk_ID_k = self.KGen(tuple(self.__group.random(ZR) for i in range(self.__l - 1)))
			print("Dec: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements where the integer $k \\in [9, {0}]$ but it is not, which has been generated randomly with a length of $9$. ".format(5 + ((self.__l - 1) << 2)))
		if isinstance(cipherText, tuple) and len(cipherText) == 4 and all([isinstance(ele, Element) for ele in cipherText]):# hybrid check
			CT = cipherText
		else:
			CT = self.Encryption(tuple(self.__group.random(ZR) for i in range(self.__l - 1)), self.__group.random(GT))
			print("Dec: The variable $\\textit{CT}$ should be a tuple containing 4 elements but it is not, which has been generated with $M \\in \\mathbb{G}_T$ generated randomly. ")
		
		# Unpack #
		A, B, C, D = CT
		a0, a1, b = sk_ID_k[0], sk_ID_k[1], sk_ID_k[2]
		
		# Scheme #
		M = pair(b, D) * A / (pair(B, a0) * pair(C, a1)) # $M \gets \cfrac{e(b, D) \cdot A}{e(B, a_0) \cdot e(C, a_1)}$
		
		# Return #
		return M # $\textbf{return }M$
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


def Scheme(curveType:tuple|list|str, n:int = 30, k:int = 10, round:int|None = None) -> list:
	# Begin #
	if isinstance(n, int) and isinstance(k, int) and 2 <= k < n:
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
			print("n =", n)
			print("k =", k)
			if isinstance(round, int) and round >= 0:
				print("round =", round)
			print("Is the system valid? No. \n\t{0}".format(e))
			return (																																														\
				([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [(curveType if isinstance(curveType, str) else None), None])		\
				+ [n, k, round if isinstance(round, int) and round >= 0 else None] + [False] * 3 + [-1] * 19																													\
			)
	else:
		print("Is the system valid? No. The parameters $n$ and $k$ should be two positive integers satisfying $2 \\leqslant k < n$. ")
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [(curveType if isinstance(curveType, str) else None), None])		\
			+ [n if isinstance(n, int) else None, k if isinstance(k, int) else None, round if isinstance(round, int) and round >= 0 else None] + [False] * 3 + [-1] * 19																	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	print("n =", n)
	print("k =", k)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeCANIFPPCT = SchemeCANIFPPCT(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeCANIFPPCT.Setup(l)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# KGen #
	startTime = perf_counter()
	ID_k = tuple(group.random(ZR) for i in range(k))
	sk_ID_k = schemeCANIFPPCT.KGen(ID_k)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DerivedKGen #
	startTime = perf_counter()
	sk_ID_kMinus1 = schemeCANIFPPCT.KGen(ID_k[:-1]) # remove the last one to generate the sk_ID_kMinus1
	sk_ID_kDerived = schemeCANIFPPCT.DerivedKGen(sk_ID_kMinus1, ID_k)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = group.random(GT)
	CT = schemeCANIFPPCT.Enc(ID_k, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec #
	startTime = perf_counter()
	M = schemeCANIFPPCT.Dec(sk_ID_k,  CT)
	MDerived = schemeCANIFPPCT.Dec(sk_ID_kDerived, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, message == MDerived, message == M]
	spaceRecords = [																																													\
		schemeCANIFPPCT.getLengthOf(group.random(ZR)), schemeCANIFPPCT.getLengthOf(group.random(G1)), schemeCANIFPPCT.getLengthOf(group.random(G2)), schemeCANIFPPCT.getLengthOf(group.random(GT)), 	\
		schemeCANIFPPCT.getLengthOf(mpk), schemeCANIFPPCT.getLengthOf(msk), schemeCANIFPPCT.getLengthOf(sk_ID_k), schemeCANIFPPCT.getLengthOf(sk_ID_kDerived), schemeCANIFPPCT.getLengthOf(CT)	\
	]
	del schemeCANIFPPCT
	print("Original:", message)
	print("Derived:", MDerived)
	print("Decrypted:", M)
	print("Is the deriver passed (message == M')? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Is the scheme correct (message == M)? {0}. ".format("Yes" if booleans[2] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, l, k, round if isinstance(round, int) else None] + booleans + timeRecords + spaceRecords

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
	roundCount, filePath = 100, "SchemeCANIFPPCT.xlsx"
	queries = ["curveType", "secparam", "l", "k", "roundCount"]
	validators = ["isSystemValid", "isDeriverPassed", "isSchemeCorrect"]
	metrics = 	[																	\
		"Setup (s)", "KGen (s)", "DerivedKGen (s)", "Enc (s)", "Dec (s)", 					\
		"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 		\
		"mpk (B)", "msk (B)", "SK (B)", "SK' (B)", "CT (B)"								\
	]
	
	# Scheme #
	qLength, columns, results = len(queries), queries + validators + metrics, []
	length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
	try:
		for curveType in curveTypes:
			for l in range(10, 31, 5):
				for k in range(5, l, 5):
					average = Scheme(curveType, l = l, k = k, round = 0)
					for round in range(1, roundCount):
						result = Scheme(curveType, l = l, k = k, round = round)
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
	iRet = EXIT_SUCCESS if results and all([all([r == roundCount for r in result[5:8]] + [r > 0 for r in result[8:length]]) for result in results]) else EXIT_FAILURE
	try:
		if isinstance(sleepingTime, float) and 0 <= sleepingTime < float("inf"):
			print("Please wait for the countdown ({0} second(s)) to end, or exit the program manually like pressing the \"Ctrl + C\" ({1}). \n".format(sleepingTime, iRet))
			sleep(sleepingTime)
		else:
			print("Please press the enter key to exit ({0}). ".format(iRet))
			input()
	except:
		print()
	return iRet



if "__main__" == __name__:
	exit(main())