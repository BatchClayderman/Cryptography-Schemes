import os
from sys import argv, exit, getsizeof
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
from time import sleep, time
try:
	from psutil import Process
except:
	print("Cannot compute the memory via ``psutil.Process``. ")
	print("Please try to install the ``psutil`` library via ``python -m pip install psutil`` or ``apt-get install python3-psutil``. ")
	print("Please press the enter key to exit. ")
	input()
	exit(-1)
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element
except:
	print("The environment of the ``charm`` library is not handled correctly. ")
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


class SchemeIBMETR:
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is only applicable to symmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		try:
			pair(self.__group.random(G1), self.__group.random(G1))
		except:
			self.__group = PairingGroup("SS512", secparam = self.__group.secparam)
			print("Init: This scheme is only applicable to symmetric groups of prime orders. The curve type has been defaulted to \"SS512\". ")
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__operand = (1 << self.__group.secparam) - 1 # use to cast binary strings
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def __product(self:object, vec:tuple|list|set) -> Element:
		if isinstance(vec, (tuple, list, set)) and vec and all([isinstance(ele, Element) for ele in vec]):
			element = vec[0]
			for ele in vec[1:]:
				element *= ele
			return element
		else:
			return self.__group.init(ZR, 1)
	def Setup(self:object) -> tuple: # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Scheme #
		p = self.__group.order() # $p \gets \|\mathbb{G}\|$
		g = self.__group.random(G1) # generate $g \in \mathbb{G}_1$ randomly
		H1 = lambda x:self.__group.hash(self.__group.serialize(x), G1) # $H_1:\{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(self.__group.serialize(x), G2) # $H_2:\{0, 1\}^* \rightarrow \mathbb{G}_2$
		if 512 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 384 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha384(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 256 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha256(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 224 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha224(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 160 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(sha1(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 128 == self.__group.secparam:
			HHat = lambda x:int.from_bytes(md5(self.__group.serialize(x)).digest(), byteorder = "big")
		else:
			HHat = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest() * ((self.__group.secparam - 1) // 512 + 1), byteorder = "big") & self.__operand # $\hat{H}: \{0, 1\}^* \rightarrow \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
		g0, g1 = self.__group.random(G1), self.__group.random(G1) # generate $g_0, g_1 \in \mathbb{G}_1$ randomly
		w, alpha, t1, t2 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $w, alpha, t_1, t_2 \in \mathbb{Z}_p^*$
		Omega = pair(g, g) ** w # $\Omega \gets e(g, g)^w$
		v1 = g ** t1 # $v \gets g^{t_1}$
		v2 = g ** t2 # $v \gets g^{t_2}$
		self.__mpk = (p, g, g0, g1, v1, v2, Omega, H1, H2, HHat) # $\textit{mpk} \gets (p, g, g_0, g_1, v_1, v_2, \Omega, H_1, H_2, \hat{H})$
		self.__msk = (w, alpha, t1, t2) # $\textit{msk} \gets (w, \alpha, t_1, t_2)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # $\textbf{return }(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, idS:Element) -> Element: # $\textbf{EKGen}(\textit{id}_S) \rightarrow \textit{ek}_{\textit{id}_S}$
		# Check #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(idS, Element) and idS.type == ZR: # type check
			id_S = idS
		else:
			id_S = self.__group.random(ZR)
			print("EKGen: The variable $\\textit{id}_S$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[-3]
		alpha = self.__msk[1]
		
		# Scheme #
		ek_id_S = H1(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_1(\textit{id}_S)$
		
		# Return #
		return ek_id_S # $\textbf{return }\textit{ek}_{\textit{id}_S}$
	def DKGen(self:object, idR:Element) -> tuple: # $\textbf{DKGen}(\textit{id}_R) \rightarrow \textit{dk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
		else:
			id_R = self.__group.random(ZR)
			print("DKGen: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1, H2 = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[-2]
		w, alpha, t1, t2 = self.__msk
		
		# Scheme #
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_p^*$ randomly
		dk0 = H2(id_R) ** alpha # $\textit{dk}_0 \gets H_2(\textit{id}_R)^\alpha$
		dk1 = g ** r # $\textit{dk}_1 \gets g^r$
		dk2 = g ** (-(w / t1)) * (g0 * g1 ** id_R) ** (-(r / t1)) # $\textit{dk}_2 \gets g^{-\frac{w}{t_1}}(g_0 g_1^{\textit{id}_R})^{-\frac{r}{t_1}}$
		dk3 = g ** (-(w / t2)) * (g0 * g1 ** id_R) ** (-(r / t2)) # $\textit{dk}_3 \gets g^{-\frac{w}{t_2}}(g_0 g_1^{\textit{id}_R})^{-\frac{r}{t_2}}$
		dk_id_R = (dk0, dk1, dk2, dk3) # $\textit{dk}_{\textit{ID}_R} \gets (\textit{dk}_0, \textit{dk}_1, \textit{dk}_2, \textit{dk}_3)$
		
		# Return #
		return dk_id_R # $\textbf{return }\textit{dk}_{\textit{id}_R}$
	def TKGen(self:object, idR:Element) -> tuple: # $\textbf{TKGen}(\textit{id}_R) \rightarrow \textit{tk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("TKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``TKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
		else:
			id_R = self.__group.random(ZR)
			print("TKGen: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1 = self.__mpk[1], self.__mpk[2], self.__mpk[3]
		t1, t2 = self.__msk[2], self.__msk[3]
		
		# Scheme #
		k = self.__group.random(ZR) # generate $k \in \mathbb{Z}_p^*$ randomly
		tk1 = g ** k # $\textit{tk}_1 \gets g^k$
		tk2 = g ** (1 / t1) * (g0 * g1 ** id_R) ** (-(k / t1)) # $\textit{tk}_2 \gets g^{\frac{1}{t_1}}(g_0 g_1^{\textit{id}_R})^{-\frac{k}{t_1}}$
		tk3 = g ** (1 / t2) * (g0 * g1 ** id_R) ** (-(k / t2)) # $\textit{tk}_3 \gets g^{\frac{1}{t_2}}(g_0 g_1^{\textit{id}_R})^{-\frac{k}{t_2}}$
		tk_id_R = (tk1, tk2, tk3) # $\textit{tk}_{\textit{ID}_R} \gets (\textit{tk}_1, \textit{tk}_2, \textit{tk}_3)$
		
		# Return #
		return tk_id_R # $\textbf{return }\textit{tk}_{\textit{id}_R}$
	def Enc(self:object, ekidS:Element, idRev:Element, message:int|bytes) -> Element: # $\textbf{Enc}(\textit{ek}_{\textit{id}_S}, \textit{id}_\textit{Rev}, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(ekidS, Element): # type check
			ek_id_S = ekidS
		else:
			ek_id_S = self.EKGen(self.__group.random(ZR))
			print("Enc: The variable $\\textit{ek}_{\\textit{id}_S}$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(idRev, Element) and idRev.type == ZR: # type check
			id_Rev = idRev
		else:
			id_Rev = self.__group.random(ZR)
			print("Enc: The variable $\\textit{id}_\textit{Rev}$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		if isinstance(message, int): # type check
			m = message & self.__operand
			if message != m:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			m = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			m = int.from_bytes(b"SchemeIBMETR", byteorder = "big")
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemeIBMETR\". ")
		
		# Unpack #
		g, g0, g1, v1, v2, Omega, H2, HHat = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[-2], self.__mpk[-1]
		
		# Scheme #
		s1, s2, beta = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $s_1, s_2, beta \in \mathbb{Z}_p^*$ randomly
		s = s1 + s2 # $s = s_1 + s_2$
		R = Omega ** -s # $R = \Omega^{-s}$
		T = g ** beta # $T \gets g^\beta$
		K = pair(H2(id_Rev), ek_id_S * T) # $K \gets e(H_2(\textit{id}_\textit{Rev}), \textit{ek}_{\textit{id}_S} \cdot T)$
		ct0 = HHat(R) ^ HHat(K) ^ m # $\textit{ct}_0 \gets \hat{H}(R) \oplus \hat{H}(K) \oplus m$
		ct1 = (g0 * g1 ** id_Rev) ** s # $\textit{ct}_1 \gets (g_0 g_1^{\textit{id}_\textit{Rev}})^s$
		ct2 = v1 ** s1 # $\textit{ct}_2 \gets v_1^{s_1}$
		ct3 = v2 ** s2 # $\textit{ct}_3 \gets v_2^{s_2}$
		V = pair(g, g) ** s # $e(g, g)^s$
		ct = (ct0, ct1, ct2, ct3, T, V) # $\textit{ct} \gets (\textit{ct}_0, \textit{ct}_1, \textit{ct}_2, \textit{ct}_3, T, V)$
		
		# Return #
		return ct # $\textbf{return }\textit{ct}$
	def Dec(self:object, dkidR:tuple, idRev:Element, idSnd:Element, cipher:tuple) -> bytes: # $\textbf{Dec}(\textit{dk}_{\textit{id}_R}, \textit{id}_\textit{Rev}, \textit{id}_\textit{Snd}, \textit{ct}) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if isinstance(idRev, Element) and idRev.type == ZR: # type check
			id_Rev = idRev
			if isinstance(dkidR, tuple) and len(dkidR) == 4 and all([isinstance(ele, Element) for ele in dkidR]): # hybrid check
				dk_id_R = dkidR
			else:
				dk_id_R = self.DKGen(id_Rev)
				print("Dec: The variable $\\textit{dk}_{\\textit{id}_R}$ should be a tuple containing 4 elements but it is not, which has been generated accordingly. ")
		else:
			id_Rev = self.__group.random(ZR)
			print("Dec: The variable $\\textit{id}_\\textit{Rev}$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
			dk_id_R = self.DKGen(id_Rev)
			print("Dec: The variable $\\textit{dk}_{\\textit{id}_R}$ has been generated accordingly. ")
		if isinstance(idSnd, Element) and idSnd.type == ZR: # type check
			id_Snd = idSnd
		else:
			id_Snd = self.__group.random(ZR)
			print("Dec: The variable $\\textit{id}_\textit{Snd}$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 6 and isinstance(cipher[0], int) and all([isinstance(ele, Element) for ele in cipher[1:]]): # hybrid check
			ct = cipher
		else:
			ct = self.Enc(self.__group.random(ZR), self.__group.random(ZR), int.from_bytes(b"SchemeIBMETR", byteorder = "big"))
			print("Dec: The variable $\\textit{ct}$ should be a tuple containing an integer and 5 elements but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1, H2, HHat = self.__mpk[-3], self.__mpk[-2], self.__mpk[-1]
		dk0, dk1, dk2, dk3 = dk_id_R
		ct0, ct1, ct2, ct3, T = ct[0], ct[1], ct[2], ct[3], ct[4]
		
		# Scheme #
		RPrime = pair(dk1, ct1) * pair(dk2, ct2) * pair(dk3, ct3) # $R' \gets e(\textit{dk}_1, \textit{ct}_1) \cdot e(\textit{dk}_2, \textit{ct}_2) \cdot e(\textit{dk}_3, \textit{ct}_3)$
		KPrime = pair(dk0, H1(id_Snd)) * pair(H2(id_Rev), T) # $K' \gets e(\textit{dk}_0, H_1(\textit{id}_\textit{Snd})) \cdot e(H_2(\textit{id}_R), T)$
		m = ct0 ^ HHat(RPrime) ^ HHat(KPrime) # $m \gets \textit{ct}_0 \oplus \hat{H}(R') \oplus \hat{H}(K')$
		
		# Return #
		return m # $\textbf{return }m$
	def TVerify(self:object, tkidR:tuple, cipher:tuple) -> bool: # $\textbf{TVerify}(\textit{tk}_{\textit{id}_R}, \textit{ct}) \rightarrow y, y \in \{0, 1\}$
		# Check #
		if not self.__flag:
			print("TVerify: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``TVerify`` subsequently. ")
			self.Setup()
		if isinstance(tkidR, tuple) and len(tkidR) == 3 and all([isinstance(ele, Element) for ele in tkidR]): # hybrid check
			tk_id_R = tkidR
		else:
			tk_id_R = self.TKGen(self.__group.random(ZR))
			print("TVerify: The variable $\\textit{tk}_{\\textit{id}_R}$ should be a tuple containing 3 elements but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 6 and isinstance(cipher[0], int) and all([isinstance(ele, Element) for ele in cipher[1:]]): # hybrid check
			ct = cipher
		else:
			ct = self.Enc(self.__group.random(ZR), self.__group.random(ZR), int.from_bytes(b"SchemeIBMETR", byteorder = "big"))
			print("TVerify: The variable $\\textit{ct}$ should be a tuple containing an integer and 5 elements but it is not, which has been generated with $m$ set to b\"SchemeIBMETR\". ")
		
		# Unpack #
		tk1, tk2, tk3 = tk_id_R
		ct1, ct2, ct3, V = ct[1], ct[2], ct[3], ct[-1]
		
		# Scheme #
		pass
		
		# Return #
		return V == pair(tk1, ct1) * pair(tk2, ct2) * pair(tk3, ct3) # $\textbf{return }V = e(\textit{tk}_1, \textit{ct}_1) \cdot e(\textit{tk}_2, \textit{ct}_2) \cdot e(\textit{tk}_3, \textit{ct}_3)$


def Scheme(curveType:tuple|list|str, round:int = None) -> list:
	# Begin #
	try:
		if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
			if curveType[1] >= 1:
				group = PairingGroup(curveType[0], secparam = curveType[1])
			else:
				group = PairingGroup(curveType[0])
		else:
			group = PairingGroup(curveType)
		pair(group.random(G1), group.random(G1))
	except BaseException as e:
		if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
			print("curveType =", curveType[0])
			if curveType[1] >= 1:
				print("secparam =", curveType[1])
		elif isinstance(curveType, str):
			print("curveType =", curveType)
		if isinstance(round, int) and round >= 0:
			print("round =", round)
		print("Is the system valid? No. {0}. ".format(e))
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [round if isinstance(round, int) else None] + [False] * 3 + [-1] * 20																																	\
		)
	process = Process(os.getpid())
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBMETR = SchemeIBMETR(group)
	timeRecords, memoryRecords = [], []
	
	# Setup #
	startTime = time()
	mpk, msk = schemeIBMETR.Setup()
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# EKGen #
	startTime = time()
	id_S = group.random(ZR)
	ek_id_S = schemeIBMETR.EKGen(id_S)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# DKGen #
	startTime = time()
	id_R = group.random(ZR)
	dk_id_R = schemeIBMETR.DKGen(id_R)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# TKGen #
	startTime = time()
	tk_id_R = schemeIBMETR.TKGen(id_R)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Enc #
	startTime = time()
	message = int.from_bytes(b"SchemeIBMETR", byteorder = "big")
	ct = schemeIBMETR.Enc(ek_id_S, id_R, message)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Dec #
	startTime = time()
	m = schemeIBMETR.Dec(dk_id_R, id_R, id_S, ct)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# TVerify #
	startTime = time()
	bRet = schemeIBMETR.TVerify(tk_id_R, ct)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# End #
	sizeRecords = [getsizeof(mpk), getsizeof(msk), getsizeof(ek_id_S), getsizeof(dk_id_R), getsizeof(tk_id_R), getsizeof(ct)]
	del schemeIBMETR
	print("Original:", message)
	print("Decrypted:", m)
	print("Is the scheme correct (message == m)? {0}. ".format("Yes" if message == m else "No"))
	print("Is the tracing verified? {0}. ".format("Yes" if bRet else "No"))
	print("Time:", timeRecords)
	print("Memory:", memoryRecords)
	print("Size:", sizeRecords)
	print()
	return [group.groupType(), group.secparam, round if isinstance(round, int) else None, True, message == m, bRet] + timeRecords + memoryRecords + sizeRecords

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
	curveTypes = (("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
	roundCount, filePath = 20, "SchemeIBMETR.xlsx"
	columns = [																				\
		"curveType", "secparam", "roundCount", "isSystemValid", "isSchemeCorrect", "isTracingVerified", 	\
		"Setup (s)", "EKGen (s)", "DKGen (s)", "TKGen (s)", "Enc (s)", "Dec (s)", "TVerify (s)", 				\
		"Setup (B)", "EKGen (B)", "DKGen (B)", "TKGen (B)", "Enc (B)", "Dec (B)", "TVerify (B)", 			\
		"mpk (B)", "msk (B)", "EK (B)", "DK (B)", "TK' (B)", "CT (B)"									\
	]
	
	# Scheme #
	length, results = len(columns), []
	try:
		roundCount = max(1, roundCount)
		for curveType in curveTypes:
			average = Scheme(curveType, 0)
			for round in range(1, roundCount):
				result = Scheme(curveType, round)
				for idx in range(3, 6):
					average[idx] += result[idx]
				for idx in range(6, 13):
					average[idx] = -1 if average[idx] < 0 or result[idx] < 0 else average[idx] + result[idx]
				for idx in range(13, length):
					average[idx] = -1 if average[idx] <= 0 or result[idx] <= 0 else average[idx] + result[idx]
			average[2] = roundCount
			for idx in range(6, length):
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
	iRet = EXIT_SUCCESS if results and all([all([r == roundCount for r in result[3:6]] + [r > 0 for r in result[6:length]]) for result in results]) else EXIT_FAILURE
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