import os
from sys import argv, exit
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
from secrets import randbelow
from time import perf_counter, sleep
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, GT, ZR, pair, pc_element as Element
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


class SchemeIBMEMR:
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
		self.__d = 30
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def __computeCoefficients(self:object, roots:tuple|list|set, k:Element|int|float|None = None) -> tuple:
		flag = False
		if isinstance(roots, (tuple, list, set)) and roots:
			n = len(roots)
			if isinstance(roots[0], Element) and all(isinstance(root, Element) and root.type == roots[0].type for root in roots):
				flag, coefficients = True, [None] * (n - 1) + [roots[0], self.__group.init(roots[0].type, 1)]
				offset = k if isinstance(k, Element) and k.type == roots[0].type else None
			elif isinstance(roots[0], (int, float)) and all(isinstance(root, (int, float)) for root in roots):
				flag, coefficients = True, [None] * (n - 1) + [roots[0], 1]
				offset = k if isinstance(k, (int, float)) else None
		if flag:
			cnt = n - 2
			for r in roots[1:]:
				coefficients[cnt] = r * coefficients[cnt + 1]
				for i in range(cnt + 1, n - 1):
					coefficients[i] += r * coefficients[i + 1]
				coefficients[n - 1] += r
				cnt -= 1
			for i in range(n - 1, -1, -2):
				coefficients[i] = -coefficients[i]
			if offset is not None:
				coefficients[0] += offset
			return tuple(coefficients)
		else:
			return (k, )
	def __concat(self:object, *vector:tuple|list) -> bytes:
		abcBytes = b""
		if isinstance(vector, (tuple, list)):
			for item in vector:
				if isinstance(item, (tuple, list)):
					abcBytes += self.__concat(*item)
				elif isinstance(item, Element):
					abcBytes += self.__group.serialize(item)
				elif isinstance(item, bytes):
					abcBytes += item
				else:
					try:
						abcBytes += bytes(item)
					except:
						pass
		return abcBytes
	def __computePolynomial(self:object, x:Element|int|float, coefficients:tuple|list) -> Element|int|float|None:
		if isinstance(coefficients, (tuple, list)) and coefficients and (															\
			isinstance(x, Element) and all(isinstance(coefficient, Element) and coefficient.type == x.type for coefficient in coefficients)	\
			or isinstance(x, (int, float)) and all(isinstance(coefficient, (int, float)) for coefficient in coefficients)						\
		):
			n, eleResult = len(coefficients) - 1, coefficients[0]
			for i in range(1, n):
				eResult = x
				for _ in range(i - 1):
					eResult *= x
				eleResult += coefficients[i] * eResult
			eResult = x
			for _ in range(n - 1):
				eResult *= x
			eleResult += eResult
			return eleResult
		else:
			return None
	def Setup(self:object, d:int = 30, seed:int|None = None) -> tuple: # $\textbf{Setup}(d) \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		if isinstance(d, int) and d >= 1: # boundary check
			self.__d = d
		else:
			self.__d = 30
			print("Setup: The variable $d$ should be a positive integer but it is not, which has been defaulted to $30$. ")
		self.__seed = seed % self.__d if isinstance(seed, int) else randbelow(self.__d)
		
		# Scheme #
		p = self.__group.order() # $p \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		H1 = lambda x:self.__group.hash(self.__group.serialize(x), G1) # $H_1: \mathbb{Z}_r \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(self.__group.serialize(x), G1) # $H_2: \mathbb{Z}_r \rightarrow \mathbb{G}_1$
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
			HHat = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest() * (((self.__group.secparam - 1) >> 9) + 1), byteorder = "big") & self.__operand # $\hat{H}: \mathbb{G}_T \rightarrow \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
		H3 = lambda x:self.__group.hash(x, ZR) # $H_3: \{0, 1\}^* \rightarrow \mathbb{Z}_r$
		H4 = lambda x:self.__group.hash(self.__group.serialize(x), ZR) # $H_4: \mathbb{G}_T \rightarrow \mathbb{Z}_r$
		H5 = lambda x:self.__group.hash(x, G1) # $H_5: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		g0, g1 = self.__group.random(G1), self.__group.random(G1) # generate $g_0, g_1 \in \mathbb{G}_1$ randomly
		w, alpha, gamma, k, t1, t2 = self.__group.random(ZR, 6) # generate $w, \alpha, \gamma, k, t_1, t_2 \in \mathbb{Z}_r$ randomly
		Omega = pair(g, g) ** w # $\Omega \gets e(g, g)^w$
		v1 = g ** t1 # $v_1 \gets g^{t_1}$
		v2 = g ** t2 # $v_2 \gets g^{t_2}$
		v3 = g ** gamma # $v_3 \gets g^\gamma$
		v4 = g ** k # $v_4 \gets g^k$
		self.__mpk = (p, g, g0, g1, v1, v2, v3, v4, Omega, H1, H2, H3, H4, H5, HHat) # $ \textit{mpk} \gets (p, g, g_0, g_1, v_1, v_2, v_3, v_4, \Omega, H_1, H_2, H_3, H_4, H_5, \hat{H})$
		self.__msk = (w, alpha, gamma, k, t1, t2) # $\textit{msk} \gets (w, \alpha, \gamma, k, t_1, t_2)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, idS:Element) -> Element: # $\textbf{EKGen}(\textit{id}_S) \rightarrow \textit{ek}_{\textit{id}_S}$
		# Check #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(idS, Element) and idS.type == ZR: # type check
			id_S = idS
		else:
			id_S = self.__group.random(ZR)
			print("EKGen: The variable $\\textit{id}_S$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[9]
		alpha = self.__msk[1]
		
		# Scheme #
		ek_id_S = H1(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_1(\textit{id}_S)^\alpha$
		
		# Return #
		return ek_id_S # \textbf{return} $\textit{ek}_{\textit{id}_S}$
	def DKGen(self:object, idR:Element) -> tuple: # $\textbf{DKGen}(\textit{id}_R) \rightarrow \textit{dk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
		else:
			id_R = self.__group.random(ZR)
			print("DKGen: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1, H2 = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[10]
		w, alpha, gamma, t1, t2 = self.__msk[0], self.__msk[1], self.__msk[2], self.__msk[4], self.__msk[5]
		
		# Scheme #
		dk1 = H2(id_R) ** alpha # $\textit{dk}_1 \gets H_2(\textit{id}_R)^\alpha$
		dk2 = g ** (w / t1) * (g0 * g1 ** id_R) ** (gamma / t1) # $\textit{dk}_2 \gets g^{w / t_1} (g_0 g_1^{\textit{id}_R})^{\gamma / t_1}$
		dk3 = g ** (w / t2) * (g0 * g1 ** id_R) ** (gamma / t2) # $\textit{dk}_3 \gets g^{w / t_2} (g_0 g_1^{\textit{id}_R})^{\gamma / t_2}$
		dk_id_R = (dk1, dk2, dk3) # $\textit{dk}_{\textit{id}_R} \gets (\textit{dk}_1, \textit{dk}_2, \textit{dk}_3)$
		
		# Return #
		return dk_id_R # \textbf{return} $\textit{dk}_{\textit{id}_R}$
	def TDKGen(self:object, idR:Element) -> tuple: # $\textbf{TDKGen}(\textit{id}_R) \rightarrow \textit{td}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("TDKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``TDKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
		else:
			id_R = self.__group.random(ZR)
			print("TDKGen: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1, H2 = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[10]
		w, alpha, k, t1, t2 = self.__msk[0], self.__msk[1], self.__msk[3], self.__msk[4], self.__msk[5]
		
		# Scheme #
		td1 = g ** (-(1 / t1)) * (g0 * g1 ** id_R) ** (k / t1) # $\textit{td}_1 \gets g^{-1 / t_1} (g_0 g_1^{\textit{id}_R})^{k / t_1}$
		td2 = g ** (-(1 / t2)) * (g0 * g1 ** id_R) ** (k / t2) # $\textit{td}_2 \gets g^{-1 / t_2} (g_0 g_1^{\textit{id}_R})^{k / t_2}$
		td_id_R = (td1, td2) # $\textit{td}_{\textit{id}_R} \gets (\textit{td}_1, \textit{td}_2)$
		
		# Return #
		return td_id_R # \textbf{return} $\textit{td}_{\textit{id}_R}$
	def Enc(self:object, ekidS:Element, idR:Element, message:int|bytes) -> object: # $\textbf{Enc}(\textit{ek}_{\textit{id}_S}, \textit{id}_R, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(ekidS, Element): # type check
			ek_id_S = ekidS
		else:
			ek_id_S = self.EKGen(self.__group.random(ZR))
			print("Enc: The variable $\\textit{ek}_{\\textit{id}_S}$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
		else:
			id_R = self.__group.random(ZR)
			print("Enc: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(message, int) and message >= 0: # type check
			m = message & self.__operand
			if message != m:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			m = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			m = int.from_bytes(b"SchemeIBMEMR", byteorder = "big")
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemeIBMEMR\". ")
		
		# Unpack #
		g, g0, g1, v1, v2, v3, v4, H2, H3, H4, H5, HHat = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[10], self.__mpk[11], self.__mpk[12], self.__mpk[13], self.__mpk[14]
		w = self.__msk[0]
		
		# Scheme #
		S = tuple(self.__group.random(ZR) for _ in range(self.__seed)) + (id_R, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - self.__seed - 1)) # generate $S \gets (\textit{id}_1, \textit{id}_2, \cdots, \textit{id}_R, \cdots, \textit{id}_d)$ randomly
		s1, s2, beta, sigma, K, R = self.__group.random(ZR, 6) # generate $s_1, s_2, \beta, \sigma, K, R \in \mathbb{Z}_r$ randomly
		r = H3(self.__group.serialize(sigma) + m.to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big")) # $r \gets H_3(\sigma || m)$
		ct1 = g ** beta # $\textit{ct}_1 \gets g^\beta$
		ct2 = v1 ** s1 # $\textit{ct}_2 \gets v_1^{s_1}$
		ct3 = v2 ** s2 # $\textit{ct}_3 \gets v_2^{s_2}$
		KArray = tuple(pair(H2(S[i]), ek_id_S * ct1) for i in range(self.__d)) # $K_i \gets e(H_2(\textit{id}_i), ek_{\textit{id}_S} \cdot \textit{ct}_1), \forall i \in \{1, 2, \cdots, d\}$
		aArray = self.__computeCoefficients(					\
			tuple(H4(KArray[i]) for i in range(self.__d)), k = K	\
		) # Compute $a_0, a_1, a_2, \cdots a_d$ that satisfy $\forall x \in \mathbb{Z}_r$, we have $F(x) = \prod\limits_{i = 1}^d (x - H_4(K_i)) + K = a_0 + \sum\limits_{i = 1}^d a_i x^i$
		s = s1 + s2 # $s \gets s_1 + s_2$
		RArray = tuple(pair(v3, (g0 * g1 ** S[i]) ** s) for i in range(self.__d)) # $R_i \gets e(v_3, (g_0 g_1^{\textit{id}_i})^s), \forall i \in \{1, 2, \cdots, d\}$
		bArray = self.__computeCoefficients(										\
			tuple(H4(RArray[i] * pair(g, g) ** (w * s)) for i in range(self.__d)), k = R		\
		) # Compute $b_0, b_1, b_2, \cdots, b_d$ that satisfy $\forall x \in \mathbb{Z}_r$, we have $L(x) = \prod\limits_{i = 1}^d (x - H_4(R_i \cdot e(g, g)^{ws})) + R = b_0 + \sum\limits_{i = 1}^d b_i x^i$
		ct4 = HHat(K) ^ HHat(R) ^ int.from_bytes(m.to_bytes((self.__group.secparam + 7) >> 3, byteorder = "big") + self.__group.serialize(sigma), byteorder = "big") # $\textit{ct}_4 \gets \hat{H}(K) \oplus \hat{H}(R) \oplus (m || \sigma)$
		VArray = tuple(pair(v4, (g0 * g1 ** S[i]) ** s) for i in range(self.__d)) # $V_i \gets e(v_4, (g_0 g_1^{\textit{id}_i})^s), \forall i \in \{1, 2, \cdots, d\}$
		cArray = self.__computeCoefficients(								\
			tuple(H4(VArray[i] * pair(g, g) ** (-s)) for i in range(self.__d))		\
		) # Compute $c_0, c_1, c_2, \cdots, c_d$ that satisfy $\forall x \in \mathbb{Z}_r$, we have $G(x) = \prod\limits_{i = 1}^d (x - H_4(V_i \cdot e(g, g)^{-s})) = c_0 + \sum\limits_{i = 1}^d c_i x^i$
		ct5 = g ** r # $\textit{ct}_5 \gets g^r$
		ct6 = H5(																					\
			self.__group.serialize(ct1) + self.__group.serialize(ct2) + self.__group.serialize(ct3) + ct4.to_bytes(		\
				((self.__group.secparam + 7) >> 3) + len(self.__group.serialize(sigma)), byteorder = "big"			\
			) + self.__group.serialize(ct5) + self.__concat(aArray, bArray, cArray)							\
		) ** r # $\textit{ct}_6 \gets H_5(\textit{ct}_1 || \textit{ct}_2 || \cdots || \textit{ct}_5 || a_0 || a_1 || \cdots || a_d || b_0 || b_1 || \cdots || b_d || c_0 || c_1 || \cdots || c_d)^r$
		ct = (ct1, ct2, ct3, ct4, ct5, ct6, aArray, bArray, cArray) # $\textit{ct} \gets (\textit{ct}_1, \textit{ct}_2, \textit{ct}_3, \textit{ct}_4, \textit{ct}_5, \textit{ct}_6)$
		
		# Return #
		return ct # \textbf{return} $\textit{ct}$
	def Dec(self:object, dkidR:tuple, idR:Element, idS:Element, cipherText:tuple) -> int|bool: # $\textbf{Dec}(\textit{dk}_{\textit{id}_R}, \textit{id}_R, \textit{id}_S, \textit{ct}) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
			if isinstance(dkidR, tuple) and len(dkidR) == 3 and all(isinstance(ele, Element) for ele in dkidR): # hybrid check
				dk_id_R = dkidR
			else:
				dk_id_R = self.DKGen(id_R)
				print("Dec: The variable $\\textit{dk}_{\\textit{id}_R}$ should be a tuple containing 3 elements but it is not, which has been generated accordingly. ")
		else:
			id_R = self.__group.random(ZR)
			print("Dec: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			dk_id_R = self.DKGen(id_R)
			print("Dec: The variable $\\textit{dk}_{\\textit{id}_R}$ has been generated accordingly. ")
		if isinstance(idS, Element) and idS.type == ZR: # type check
			id_S = idS
		else:
			id_S = self.__group.random(ZR)
			print("Dec: The variable $\\textit{id}_S$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if (																																															\
			isinstance(cipherText, tuple) and len(cipherText) == 9 and all(isinstance(ele, Element) for ele in cipherText[:3]) and isinstance(cipherText[3], int) and isinstance(cipherText[4], Element) and isinstance(cipherText[5], Element)		\
			and all(isinstance(ele, tuple) and len(ele) >= 1 and all(isinstance(sEle, Element) and sEle.type == ZR for sEle in ele) for ele in cipherText[6:]) and len(cipherText[6]) == len(cipherText[7]) == len(cipherText[8])					\
		): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.EKGen(id_S), id_R, int.from_bytes(b"SchemeIBMEMR", byteorder = "big"))
			print("Dec: The variable $\\textit{ct}$ should be a tuple containing 9 objects but it is not, which has been generated with $m$ set to b\"SchemeIBMEMR\". ")
		
		# Unpack #
		g, H1, H2, H3, H4, H5, HHat = self.__mpk[1], self.__mpk[9], self.__mpk[10], self.__mpk[11], self.__mpk[12], self.__mpk[13], self.__mpk[14]
		dk1, dk2, dk3 = dk_id_R
		ct1, ct2, ct3, ct4, ct5, ct6, aArray, bArray, cArray = ct
		
		# Scheme #
		if pair(																								\
			ct5, H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + self.__group.serialize(ct3) + ct4.to_bytes(			\
				((self.__group.secparam + 7) >> 3) + len(self.__group.serialize(self.__group.random(ZR))), byteorder = "big"		\
			) + self.__group.serialize(ct5) + self.__concat(aArray, bArray, cArray)) 										\
		) == pair(ct6, g): # \textbf{if} $e(\textit{ct}_5, H_5(\textit{ct}_1 || \textit{ct}_2 || \cdots || \textit{ct}_5 || a_0 || a_1 || \cdots || a_d || b_0 || b_1 || \cdots || b_d || c_0 || c_1 || \cdots c_d)) = e(\textit{ct}_6, g)$ \textbf{then}
			KPrimePrime = H4(pair(dk1, H1(id_S)) * pair(H2(id_R), ct1)) # \quad$K'' \gets H_4(e(\textit{dk}_1, H_1(\textit{id}_S)) \cdot e(H_2(\textit{id}_R), \textit{ct}_1))$
			RPrimePrime = H4(pair(dk2, ct2) * pair(dk3, ct3)) # \quad$R'' \gets H_4(e(\textit{dk}_2, \textit{ct}_2) \cdot e(\textit{dk}_3, \textit{ct}_3))$
			KPrime = self.__computePolynomial(KPrimePrime, aArray) # \quad$K' \gets \sum\limits_{i = 0}^d a_i K''^i$
			RPrime = self.__computePolynomial(RPrimePrime, bArray) # \quad$R' \gets \sum\limits_{i = 0}^d b_i R''^i$
			token = len(self.__group.serialize(self.__group.random(ZR)))
			m_sigma = (ct4 ^ HHat(KPrime) ^ HHat(RPrime)).to_bytes(((self.__group.secparam + 7) >> 3) + token, byteorder = "big") # \quad$m || \sigma \gets \textit{ct}_4 \oplus \hat{H}(K') \oplus \hat(H)(R')$
			r = H3(m_sigma) # \quad$r \gets H_3(m || \sigma)$
			if ct5 != g ** r: # \quad\textbf{if} $\textit{ct}_5 \neq g^r$ \textbf{then}
				m = False # \quad\quad$m \gets \perp$
			else:
				m = int.from_bytes(m_sigma[:-token], byteorder = "big")
			# \quad\textbf{end if}
		else: # \textbf{else}
			m = False # \quad$m \gets \perp$
		# \textbf{end if}
		
		# Return #
		return m # \textbf{return} $m$
	def ReceiverVerify(self:object, cipherText:tuple, tdidR:tuple) -> bool: # $\textbf{ReceiverVerify}(\textit{ct}, \textit{td}_{\textit{id}_R}) \rightarrow y, y \in \{0, 1\}$
		# Check #
		if (																																															\
			isinstance(cipherText, tuple) and len(cipherText) == 9 and all(isinstance(ele, Element) for ele in cipherText[:3]) and isinstance(cipherText[3], int) and isinstance(cipherText[4], Element) and isinstance(cipherText[5], Element)		\
			and all(isinstance(ele, tuple) and len(ele) >= 1 and all(isinstance(sEle, Element) and sEle.type == ZR for sEle in ele) for ele in cipherText[6:]) and len(cipherText[6]) == len(cipherText[7]) == len(cipherText[8])					\
		): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.EKGen(self.__group.random(ZR)), self.__group.random(ZR), int.from_bytes(b"SchemeIBMEMR", byteorder = "big"))
			print("ReceiverVerify: The variable $\\textit{ct}$ should be a tuple containing 9 objects but it is not, which has been generated with $m$ set to b\"SchemeIBMEMR\". ")
		if isinstance(tdidR, tuple) and len(tdidR) == 2 and isinstance(tdidR[0], Element) and isinstance(tdidR[1], Element):
			td_id_R = tdidR
		else:
			td_id_R = self.TDKGen(self.__group.random(ZR))
			print("ReceiverVerify: The variable $\\textit{td}_{\textit{id}_R}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, H4, H5 = self.__mpk[1], self.__mpk[12], self.__mpk[13]
		ct1, ct2, ct3, ct4, ct5, ct6, aArray, bArray , cArray = ct
		td1, td2 = td_id_R
		
		# Scheme #
		if pair(																								\
			ct5, H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + self.__group.serialize(ct3) + ct4.to_bytes(			\
				((self.__group.secparam + 7) >> 3) + len(self.__group.serialize(self.__group.random(ZR))), byteorder = "big"		\
			) + self.__group.serialize(ct5) + self.__concat(aArray, bArray, cArray)) 										\
		) == pair(ct6, g): # \textbf{if} $e(\textit{ct}_5, H_5(\textit{ct}_1 || \textit{ct}_2 || \cdots || \textit{ct}_5 || a_0 || a_1 || \cdots || a_d || b_0 || b_1 || \cdots || b_d || c_0 || c_1 || \cdots c_d)) = e(\textit{ct}_6, g)$ \textbf{then}
			VPrime = H4(pair(td1, ct2) * pair(td2, ct3)) # \quad$V' \gets H_4(e(\textit{td}_1, \textit{ct}_2) \cdot e(\textit{td}_2, \textit{ct}_3))$
			y = self.__computePolynomial(VPrime, cArray) == self.__group.init(ZR, 0) # \quad$y \gets \sum\limits_{i = 0}^d c_i V'^i = 0$
		else: # \textbf{else}
			y = False # \quad$y \gets 0$
		# \textbf{end if}
		
		# Return #
		return y # \textbf{return} $y$
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


def Scheme(curveType:tuple|list|str, d:int = 30, round:int|None = None) -> list:
	# Begin #
	if isinstance(d, int) and d >= 1: # no need to check the parameters for curve types here
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
			else:
				print("curveType = Unknown")
			print("d =", d)
			if isinstance(round, int) and round >= 0:
				print("round =", round)
			print("Is the system valid? No. \n\t{0}".format(e))
			return (																																													\
				([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])	\
				+ [d if isinstance(d, int) else None, round if isinstance(round, int) else None] + [False] * 3 + [-1] * 16																										\
			)
	else:
		print("Is the system valid? No. The parameter $d$ should be a positive integer. ")
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [d if isinstance(d, int) else None, round if isinstance(round, int) and round >= 0 else None] + [False] * 3 + [-1] * 16																							\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	print("d =", d)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBMEMR = SchemeIBMEMR(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBMEMR.Setup(d = d)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# EKGen #
	startTime = perf_counter()
	id_S = group.random(ZR)
	ek_id_S = schemeIBMEMR.EKGen(id_S)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DKGen #
	startTime = perf_counter()
	id_R = group.random(ZR)
	dk_id_R = schemeIBMEMR.DKGen(id_R)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# TDKGen #
	startTime = perf_counter()
	td_id_R = schemeIBMEMR.TDKGen(id_R)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = int.from_bytes(b"SchemeIBMEMR", byteorder = "big")
	ct = schemeIBMEMR.Enc(ek_id_S, id_R, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec #
	startTime = perf_counter()
	m = schemeIBMEMR.Dec(dk_id_R, id_R, id_S, ct)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# ReceiverVerify #
	startTime = perf_counter()
	bRet = schemeIBMEMR.ReceiverVerify(ct, td_id_R)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(m, bool) and message == m, bRet]
	spaceRecords = [																														\
		schemeIBMEMR.getLengthOf(group.random(ZR)), schemeIBMEMR.getLengthOf(group.random(G1)), schemeIBMEMR.getLengthOf(group.random(GT)), 	\
		schemeIBMEMR.getLengthOf(mpk), schemeIBMEMR.getLengthOf(msk), schemeIBMEMR.getLengthOf(ek_id_S),  									\
		schemeIBMEMR.getLengthOf(dk_id_R), schemeIBMEMR.getLengthOf(td_id_R), schemeIBMEMR.getLengthOf(ct)									\
	]
	del schemeIBMEMR
	print("Original:", message)
	print("Decrypted:", m)
	print("Is the scheme correct (message == m)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Is the tracing verified? {0}. ".format("Yes" if booleans[2] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, d, round if isinstance(round, int) else None] + booleans + timeRecords + spaceRecords

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
	roundCount, filePath = 100, "SchemeIBMEMR.xlsx"
	queries = ["curveType", "secparam", "d", "roundCount"]
	validators = ["isSystemValid", "isSchemeCorrect", "isTracingVerified"]
	metrics = 	[																				\
		"Setup (s)", "EKGen (s)", "DKGen (s)", "TDKGen (s)", "Enc (s)", "Dec (s)", "ReceiverVerify (s)", 		\
		"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 								\
		"mpk (B)", "msk (B)", "ek_id_S (B)", "dk_id_R (B)", "td_id_R (B)", "ct (B)"						\
	]
	
	# Scheme #
	qLength, columns, results = len(queries), queries + validators + metrics, []
	length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
	try:
		for curveType in curveTypes:
			for d in range(5, 31, 5):
				average = Scheme(curveType, d = d, round = 0)
				for round in range(1, roundCount):
					result = Scheme(curveType, d = d, round = round)
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
	iRet = EXIT_SUCCESS if results and all(all(tuple(r == roundCount for r in result[3:7]) + tuple(r > 0 for r in result[7:length])) for result in results) else EXIT_FAILURE
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