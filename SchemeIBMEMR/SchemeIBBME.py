import os
from sys import argv, exit
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


class SchemeIBBME:
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
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
	def __computeCoefficients(self:object, roots:tuple|list|set, w:Element|int|float|None = None) -> tuple:
		flag = False
		if isinstance(roots, (tuple, list, set)) and roots:
			d = len(roots)
			if isinstance(roots[0], Element) and all(isinstance(root, Element) and root.type == roots[0].type for root in roots):
				flag, coefficients = True, [self.__group.init(roots[0].type, 1), roots[0]] + [None] * (d - 1)
				constant = w if isinstance(w, Element) and w.type == roots[0].type else None
			elif isinstance(roots[0], (int, float)) and all(isinstance(root, (int, float)) for root in roots) and isinstance(w, (int, float)):
				flag, coefficients = True, [1, roots[0]] + [None] * (d - 1)
				constant = w if isinstance(w, (int, float)) else None
		if flag:
			cnt = 2
			for r in roots[1:]:
				coefficients[cnt] = r * coefficients[cnt - 1]
				for k in range(cnt - 1, 1, -1):
					coefficients[k] += r * coefficients[k - 1]
				coefficients[1] += r
				cnt += 1
			if constant is not None:
				coefficients[-1] += -constant if d & 1 else constant
			return tuple(-coefficients[i] if i & 1 else coefficients[i] for i in range(d, -1, -1))
		else:
			return (w, )
	def __computePolynomial(self:object, x:Element|int|float, coefficients:tuple|list) -> Element|int|float|None:
		if isinstance(coefficients, (tuple, list)) and coefficients and (															\
			isinstance(x, Element) and all(isinstance(coefficient, Element) and coefficient.type == x.type for coefficient in coefficients)	\
			or isinstance(x, (int, float)) and all(isinstance(coefficient, (int, float)) for coefficient in coefficients)						\
		):
			d, eleResult = len(coefficients) - 1, coefficients[0]
			for i in range(1, d):
				eResult = x
				for _ in range(i - 1):
					eResult *= x
				eleResult += coefficients[i] * eResult
			eResult = x
			for _ in range(d - 1):
				eResult *= x
			eleResult += eResult
			return eleResult
		else:
			return None
	def Setup(self:object, l:int = 30) -> tuple: # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		if isinstance(l, int) and l > 0: # boundary check
			self.__l = l
		else:
			self.__l = 30
			print("Setup: The variable $l$ should be a positive integer but it is not, which has been defaulted to $30$. ")

		# Scheme #
		g, v = self.__group.random(G1), self.__group.random(G1) # generate $g, v \in \mathbb{G}_1$ randomly
		h = self.__group.random(G2) # generate $h \in \mathbb{G}_2$ randomly
		r1 = tuple(self.__group.random(ZR) for _ in range(self.__l + 1)) # generate $\vec{r}_1 = (r_{1, 0}, r_{1, 1}, \cdots, r{1, l}) \in \mathbb{Z}_r^{l + 1}$ randomly
		r2 = tuple(self.__group.random(ZR) for _ in range(self.__l + 1)) # generate $\vec{r}_2 = (r_{2, 0}, r_{2, 1}, \cdots, r{2, l}) \in \mathbb{Z}_r^{l + 1}$ randomly
		t1, t2, beta1, beta2, alpha, rho, b, tau = self.__group.random(ZR, 8) # generate $t_1, t_2, \beta_1, \beta_2, \alpha, \rho, b, \tau \in \mathbb{Z}_r$ randomly
		r = tuple(r1[i] + b * r2[i] for i in range(self.__l + 1)) # $\vec{r} = (r_0, r_1, \cdots, r_l) \gets \vec{r}_1 + b\vec{r}_2 = (r_{1, 0} + br_{2, 0}, r_{1, 1} + br_{2, 1}, \cdots, r_{1, l} + br_{2, l})$
		t = t1 + b * t2 # $t \gets t_1 + bt_2$
		beta = beta1 + b * beta2 # $\beta \gets \beta_1 + b\beta_2$
		R = tuple(g ** r[i] for i in range(self.__l + 1)) # $\vec{R} \gets g^\vec{r} = (g^{r_0}, g^{r_1}, \cdots, g^{r_l})$
		T = g ** t # $T \gets g^t$
		H0 = lambda x:self.__group.hash(x, G2) # $H_0: \{0, 1\}^* \rightarrow \mathbb{G}_2$
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, ZR) # $H_2: \{0, 1\}^* \rightarrow \mathbb{Z}_r$
		H3 = lambda x:self.__group.hash(self.__group.serialize(x), ZR) # $H_3: \mathbb{G}_T \rightarrow \mathbb{Z}_r$
		self.__mpk = (																																													\
			v, v ** rho, g, g ** b, R, T, pair(g, h) ** beta, h, tuple(h ** r1[i] for i in range(l + 1)), tuple(h ** r2[i] for i in range(l + 1)), h ** t1, h ** t2, g ** (tau * beta), h ** (tau * beta1), h ** (tau * beta2), h ** (1 / tau), H0, H1, H2, H3		\
		) # $\textit{mpk} \gets (v, v^\rho, g, g^b, \vec{R}, T, e(g, h)^\beta, h, h^{\vec{r}_1}, h^{\vec{r}_2}, h^{t_1}, h^{t_2}, g^{\tau\beta}, h^{\tau\beta_1}, h^{\tau\beta_2}, h^{1/\tau}, H_0, H_1, H_2, H_3)$
		self.__msk = (h ** beta1, h ** beta2, alpha, rho) # $\textit{msk} \gets (h^{\beta_1}, h^{\beta_2}, \alpha, \rho)$
		
		# Return #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, _idStar:bytes) -> Element: # $\textbf{EKGen}(\textit{id}^*) \rightarrow \textit{ek}_{\textit{id}^*}$
		# Check #
		if not self.__flag:
			self.Setup()
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
		if isinstance(_idStar, bytes): # type check
			idStar = _idStar
		else:
			idStar = randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big")
			print("EKGen: The variable $\textit{id}^*$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[17]
		alpha = self.__msk[2]
		
		# Scheme #
		ek_idStar = H1(idStar) ** alpha # $\textit{ek}_{\textit{id}^*} \gets H_1(\textit{id}^*)^\alpha$
		
		# Return #
		return ek_idStar # \textbf{return} $\textit{ek}_{\textit{id}^*}$
	def DKGen(self:object, _identity:bytes) -> Element: # $\textbf{DKGen}(\textit{id}) \rightarrow \textit{dk}_\textit{id}$
		# Check #
		if not self.__flag:
			self.Setup()
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
		if isinstance(_identity, bytes): # type check
			identity = _identity
		else:
			identity = randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big")
			print("DKGen: The variable $\textit{id}$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		h, hToThePowerOfR1, hToThePowerOfR2, hToThePowerOfT1, hToThePowerOfT2, H0, H2 = self.__mpk[7], self.__mpk[8], self.__mpk[9], self.__mpk[10], self.__mpk[11], self.__mpk[16], self.__mpk[18]
		hToThePowerOfBeta1, hToThePowerOfBeta2, alpha, rho = self.__msk
		
		# Scheme #
		z = self.__group.random(ZR) # generate $z \in \mathbb{Z}_r$ randomly
		rtags = tuple(self.__group.random(ZR) for _ in range(self.__l)) # generate $\textit{rtags} = (\textit{rtag}_1, \textit{rtag}_2, \cdots, \textit{rtag}_l) \in \mathbb{Z}_r^l$ randomly
		dk1 = H0(identity) ** rho # $\textit{dk}_1 \gets H_0(\textit{id})^\rho$
		dk2 = H0(identity) ** alpha # $\textit{dk}_2 \gets H_0(\textit{id})^\alpha$
		dk3 = H0(identity) # $\textit{dk}_3 \gets H_0(\textit{id})$
		dk4 = hToThePowerOfBeta1 * hToThePowerOfT1 ** z # $\textit{dk}_4 \gets h^{\beta_1}(h^{t_1})^z$
		dk5 = hToThePowerOfBeta2 * hToThePowerOfT2 ** z # $\textit{dk}_5 \gets h^{\beta_2}(h^{t_2})^z$
		dk6 = h ** z # $\textit{dk}_6 \gets h^z$
		dk7 = tuple(																												\
			(hToThePowerOfT1 ** rtags[j - 1] * hToThePowerOfR1[j] / hToThePowerOfR1[0] ** (H2(identity) ** j)) ** z for j in range(1, self.__l + 1)		\
		) # $\textit{dk}_{7, j} \gets ((h^{t_1})^{\textit{rtag}_j}h^{r_{1, j}} / (h^{r_{1, 0}})^{H_2(\textit{id})^j})^z, \forall j \in \{1, 2, \cdots, l\}$
		dk8 = tuple(																												\
			(hToThePowerOfT2 ** rtags[j - 1] * hToThePowerOfR2[j] / hToThePowerOfR2[0] ** (H2(identity) ** j)) ** z for j in range(1, self.__l + 1)		\
		) # $\textit{dk}_{8, j} \gets ((h^{t_2})^{\textit{rtag}_j}h^{r_{2, j}} / (h^{r_{2, 0}})^{H_2(\textit{id})^j})^z, \forall j \in \{1, 2, \cdots, l\}$
		dk_id = (dk1, dk2, dk3, dk4, dk5, dk6, dk7, dk8, rtags) # $\textit{dk}_\textit{id} \gets (\textit{dk}_1, \textit{dk}_2, \cdots, \textit{dk}_8, \textit{rtags})$
		
		# Return #
		return dk_id # \textbf{return} $\textit{dk}_\textit{id}$
	def Enc(self:object, _S:tuple, ekidStar:Element, message:Element) -> tuple: # $\textbf{Enc}(S, \textit{ek}_{\textit{id}^*}, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			self.Setup()
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
		if isinstance(_S, tuple) and _S and all(isinstance(ele, bytes) for ele in _S):
			S = _S
		else:
			S = tuple(randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big") for _ in range(self.__l))
			print("Enc: The variable $S$ should be a tuple containing $n$ ``bytes`` objects but it is not, which has been generated randomly with $n$ set to $l$. ")
		if isinstance(ekidStar, Element) and ekidStar.type == G1: # type check
			ek_idStar = ekidStar
		else:
			ek_idStar = self.EKGen(randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big"))
			print("Enc: The variable $\textit{ek}_{\textit{id}^*}$ should be an element of $\\mathbb{G}_1$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			m = message
		else:
			m = self.__group.random(GT)
			print("Enc: The variable $m$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		H = self.__mpk[-2]
		P, P0 = self.__mpk[0], self.__mpk[1]
		
		# Scheme #
		y = self.__computeCoefficients(tuple(H2(ele) for ele in S)) # Compute $y_0, y_1, y_2, \cdots y_n$ that satisfy $\forall x \in \mathbb{R}$, we have $F(x) = \prod\limits_{i = 1}^n (x - H_2(S_i)) = y_0 + \sum\limits_{i = 1}^n y_i x^i$
		T = t * P # $T \gets t \cdot P$
		U = u * P # $U \gets u \cdot P$
		H_R = H(R) # $H_R \gets H(R)$
		k_R = pair(H_R, u * P0) # $k_R \gets e(H_R, u \cdot P_0)$
		k_S = pair(H_R, T + ek_S) # $k_S \gets e(H_R, T + \textit{ek}_S)$
		V = M ^ int.from_bytes(self.__group.serialize(k_R), byteorder = "big") ^ int.from_bytes(self.__group.serialize(k_S), byteorder = "big") # $V \gets M \oplus k_R \oplus k_S$
		C = (T, U, V) # $C \gets (T, U, V)$
		
		# Return #
		return C # \textbf{return} $C$	
	def Dec(self:object, dkR:tuple, sender:Element, cipher:tuple) -> int: # $\textbf{Dec}(\textit{dk}_R, S, C) \rightarrow M$
		# Check #
		if not self.__flag:
			self.Setup()
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
		if isinstance(dkR, tuple) and len(dkR) == 3 and all(isinstance(ele, Element) for ele in dkR): # hybrid check
			dk_R = dkR
		else:
			dk_R = self.DKGen(self.__group.random(ZR))
			print("Dec: The variable $\\textit{dk}_R$ should be a tuple containing 3 elements but it is not, which has been generated randomly. ")
		if isinstance(sender, Element) and sender.type == ZR: # type check
			S = sender
		else:
			S = self.__group.random(ZR)
			print("Dec: The variable $S$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 3 and isinstance(cipher[0], Element) and isinstance(cipher[1], Element) and isinstance(cipher[2], int): # hybrid check
			C = cipher
		else:
			C = self.Enc(self.EKGen(self.__group.random(ZR)), self.__group.random(ZR), b"SchemeIBBME")
			print("Dec: The variable $C$ should be a tuple containing 2 elements and an ``int`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		HPrime = self.__mpk[-1]
		dk1, dk2, dk3 = dk_R
		T, U, V = C
		
		# Scheme #
		k_R = pair(dk1, U) # $k_R \gets e(\textit{dk}_1, U)$
		HPrime_S = HPrime(S) # $H'_S \gets H'(S)$
		k_S = pair(dk3, T) * pair(HPrime_S, dk2) # $k_S \gets e(\textit{dk}_3, T)$
		M = V ^ int.from_bytes(self.__group.serialize(k_R), byteorder = "big") ^ int.from_bytes(self.__group.serialize(k_S), byteorder = "big") # $M \gets V \oplus k_R \oplus k_S$
		
		# Return #
		return M # \textbf{return} $M$
	def getLengthOf(self:object, obj:Element|tuple|list|set|bytes|int) -> int:
		if isinstance(obj, Element):
			return len(self.__group.serialize(obj))
		elif isinstance(obj, (tuple, list, set)):
			sizes = tuple(self.getLengthOf(o) for o in obj)
			return -1 if -1 in sizes else sum(sizes)
		elif isinstance(obj, bytes):
			return len(obj)
		elif isinstance(obj, int) or callable(obj):
			return (self.__group.secparam + 7) >> 3
		else:
			return -1


def Scheme(curveType:tuple|list|str, n:int = 30, round:int = None) -> list:
	# Begin #
	if isinstance(n, int) and n > 0: # no need to check the parameters for curve types here
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
			if isinstance(round, int) and round >= 0:
				print("round =", round)
			print("Is the system valid? No. \n\t{0}".format(e))
			return (																																														\
				([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
				+ [n if isinstance(n, int) else None, round if isinstance(round, int) else None] + [False] * 2 + [-1] * 13																											\
			)
	else:
		print("Is the system valid? No. The parameter $n$ should be a positive integer. ")
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [n if isinstance(n, int) else None, round if isinstance(round, int) and round >= 0 else None] + [False] * 2 + [-1] * 13																							\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBBME = SchemeIBBME(group)
	timeRecords = []

	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBBME.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# EKGen #
	startTime = perf_counter()
	idStar = randbelow(1 << group.secparam).to_bytes((group.secparam + 7) >> 3, byteorder = "big")
	ek_idStar = schemeIBBME.EKGen(idStar)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DKGen #
	startTime = perf_counter()
	identity = randbelow(1 << group.secparam).to_bytes((group.secparam + 7) >> 3, byteorder = "big")
	dk_id = schemeIBBME.DKGen(identity)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	S = tuple(randbelow(1 << group.secparam).to_bytes((group.secparam + 7) >> 3, byteorder = "big") for _ in range(n))
	message = group.random(GT)
	ct = schemeIBBME.Enc(S, ek_idStar, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec #
	startTime = perf_counter()
	M = schemeIBBME.Dec(dk_R, S, C)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, message == M]
	spaceRecords = [																																				\
		schemeIBBME.getLengthOf(group.random(ZR)), schemeIBBME.getLengthOf(group.random(G1)), schemeIBBME.getLengthOf(group.random(GT)), 								\
		schemeIBBME.getLengthOf(mpk), schemeIBBME.getLengthOf(msk), schemeIBBME.getLengthOf(ek_idStar), schemeIBBME.getLengthOf(dk_R), schemeIBBME.getLengthOf(C)		\
	]
	del schemeIBBME
	print("Original:", message)
	print("Decrypted:", M)
	print("Is the scheme correct (message == M)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, round if isinstance(round, int) else None] + booleans + timeRecords + spaceRecords

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
	roundCount, filePath = 100, "SchemeIBBME.xlsx"
	queries = ["curveType", "secparam", "roundCount"]
	validators = ["isSystemValid", "isSchemeCorrect"]
	metrics = 	[													\
		"Setup (s)", "EKGen (s)", "DKGen (s)", "Enc (s)", "Dec (s)", 		\
		"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 	\
		"mpk (B)", "msk (B)", "ek_idStar (B)", "dk_R (B)", "C (B)"		\
	]
	
	# Scheme #
	qLength, columns, results = len(queries), queries + validators + metrics, []
	length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
	try:
		for curveType in curveTypes:
			average = Scheme(curveType, 0)
			for round in range(1, roundCount):
				result = Scheme(curveType, round)
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
	#except BaseException as e:
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
	iRet = EXIT_SUCCESS if results and all(all(tuple(r == roundCount for r in result[3:5]) + tuple(r > 0 for r in result[5:length])) for result in results) else EXIT_FAILURE
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