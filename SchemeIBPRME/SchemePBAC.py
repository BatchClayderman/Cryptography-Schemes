import os
from sys import argv, exit
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
from math import ceil, log
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


class SchemePBAC:
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
	def Setup(self:object) -> tuple: # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Scheme #
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		s, alpha = self.__group.random(ZR), self.__group.random(ZR) # generate $s, \alpha \in \mathbb{Z}_r$ randomly
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, G1) # $H_2: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H3 = lambda x1, x2, x3:self.__group.hash(																	\
			self.__group.serialize(x1) + self.__group.serialize(x2) + (self.__group.serialize(x3) if isinstance(x3, Element) else (		\
				x3.to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") if isinstance(x3, int) else bytes(x3)				\
			)), ZR																							\
		) # $H_3: \mathbb{G}_T^2 \times \{0, 1\}^\lambda \rightarrow \mathbb{Z}_r$
		if 512 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 384 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha384(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 256 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha256(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 224 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha224(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 160 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(sha1(self.__group.serialize(x)).digest(), byteorder = "big")
		elif 128 == self.__group.secparam:
			H4 = lambda x:int.from_bytes(md5(self.__group.serialize(x)).digest(), byteorder = "big")
		else:
			H4 = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest() * ceil(self.__group.secparam / 512), byteorder = "big") & self.__operand # $H_4: \{0, 1\}^* \rightarrow \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
		H5 = lambda x:self.__group.hash(x, G1) # $H_5: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H6 = lambda x:self.__group.hash(x, G1) # $H_6: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		gHat = g ** s # $\hat{g} \gets g^s$
		self.__mpk = (g, gHat, H1, H2, H3, H4, H5, H6) # $ \textit{mpk} \gets (g, \hat{g}, H_1, H_2, H_3, H_4, H_5, H_6)$
		self.__msk = (s, alpha) # $\textit{msk} \gets (s, \alpha)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def SKGen(self:object, idS:bytes) -> Element: # $\textbf{SKGen}(\textit{id}_S) \rightarrow \textit{ek}_{\textit{id}_S}$
		# Check #
		if not self.__flag:
			print("SKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``SKGen`` subsequently. ")
			self.Setup()
		if isinstance(idS, bytes): # type check
			id_S = idS
		else:
			id_S = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("SKGen: The variable $\\textit{id}_S$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[2]
		alpha = self.__msk[-1]
		
		# Scheme #
		ek_id_S = H1(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_1(\textit{id}_S)^\alpha$
		
		# Return #
		return ek_id_S # \textbf{return} $\textit{ek}_{\textit{id}_S}$
	def RKGen(self:object, idR:bytes) -> tuple: # $\textbf{RKGen}(\textit{id}_R) \rightarrow \textit{dk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("RKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``RKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, bytes): # type check
			id_R = idR
		else:
			id_R = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("RKGen: The variable $\\textit{id}_R$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H2 = self.__mpk[3]
		s, alpha = self.__msk
		
		# Scheme #
		dk_id_R1 = H2(id_R) ** alpha # $\textit{dk}_{\textit{id}_R, 1} \gets H_2(\textit{id}_R)^\alpha$
		dk_id_R2 = H2(id_R) ** s # $\textit{dk}_{\textit{id}_R, 2} \gets H_2(\textit{id}_R)^s$
		dk_id_R = (dk_id_R1, dk_id_R2) # $\textit{dk}_{\textit{id}_R} \gets (\textit{dk}_{\textit{id}_R, 1}, \textit{dk}_{\textit{id}_R, 2})$
		
		# Return #
		return dk_id_R # \textbf{return} $\textit{dk}_{\textit{id}_R}$
	def Enc(self:object, ekid1:Element, id2:Element, message:int|bytes) -> tuple: # $\textbf{Enc}(\textit{ek}_{\textit{id}_1}, \textit{id}_2, m) \rightarrow C$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(ekid1, Element): # type check
			ek_id_1 = ekid1
		else:
			ek_id_1 = self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("Enc: The variable $\\textit{ek}_{\\textit{id}_1}$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Enc: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(message, int) and message >= 0: # type check
			m = message & self.__operand
			if message != m:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			m = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			m = int.from_bytes(b"SchemePBAC", byteorder = "big") & self.__operand
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemePBAC\". ")
		
		# Unpack #
		g, gHat, H2, H3, H4, H5 = self.__mpk[0], self.__mpk[1], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6]
		
		# Scheme #
		eta_1, eta_2 = self.__group.random(GT), self.__group.random(GT) # generate $\eta_1, \eta_2 \in \mathbb{G}_T$ randomly
		r = H3(eta_1, eta_2, m) # $r \gets H_3(\eta_1, \eta_2, m)$
		C1 = g ** r # $C_1 \gets g^r$
		C2 = eta_1 * pair(gHat, H2(id_2) ** r) # $C_2 \gets \eta_1 \cdot e(\hat{g}, H_2(\textit{id}_2)^r)$
		C3 = eta_2 * pair(ek_id_1, H2(id_2)) # $C_3 \gets \eta_2 \cdot e(\textit{ek}_{\textit{id}_1}, H_2(\textit{id}_2))$
		C4 = m ^ H4(eta_1) ^ H4(eta_2) # $C_4 \gets m \oplus H_4(\eta_1) \oplus H_4(\eta_2)$
		S = H5(id_2 + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + C4.to_bytes(ceil(log(C4 + 1, 256)), byteorder = "big")) ** r # $S \gets H_5(\textit{id}_2 || C_1 || C_2 || C_3 || C_4)^r$
		C = (C1, C2, C3, C4, S) # $C \gets (C_1, C_2, C_3, C_4, S)$
		
		# Return #
		return C # \textbf{return} $C$
	def PKGen(self:object, ekid2:Element, dkid2:tuple, id1:bytes, id2:bytes, id3:bytes) -> tuple: # $\textbf{PKGen}(\textit{ek}_{\textit{id}_2}, \textit{dk}_{\textit{id}_2}, \textit{id}_1, \textit{id}_2, \textit{id}_3) \rightarrow \textit{rk}$
		# Check #
		if not self.__flag:
			print("PKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``PKGen`` subsequently. ")
			self.Setup()
		if isinstance(id2, bytes): # type check:
			id_2 = id2
			if isinstance(ekid2, Element): # type check
				ek_id_2 = ekid2
			else:
				ek_id_2 = self.SKGen(id_2)
				print("PKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ should be an element but it is not, which has been generated accordingly. ")
			if isinstance(dkid2, tuple) and len(dkid2) == 2 and all(isinstance(ele, Element) for ele in dkid2): # hybrid check
				dk_id_2 = dkid2
			else:
				dk_id_2 = self.RKGen(id_2)
				print("PKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated accordingly. ")
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			ek_id_2 = self.SKGen(id_2)
			print("PKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ has been generated accordingly. ")
			dk_id_2 = self.RKGen(id_2)
			print("PKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(id3, bytes): # type check
			id_3 = id3
		else:
			id_3 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\textit{id}_3$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H2, H6 = self.__mpk[3], self.__mpk[7]
		
		# Scheme #
		N1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") # generate $N_1 \in \{0, 1\}^\lambda$ randomly
		N2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") # generate $N_2 \in \{0, 1\}^\lambda$ randomly
		K1 = pair(dk_id_2[1], H2(id_3)) # $K_1 \gets e(\textit{dk}_{\textit{id}_2, 2}, H_2(\textit{id}_3))$
		K2 = pair(ek_id_2, H2(id_3)) # $K_2 \gets e(\textit{ek}_{\textit{id}_2}, H_2(\textit{id}_3))$
		rk_1 = (N1, H6(self.__group.serialize(K1) + id_2 + id_3 + N1) * dk_id_2[1]) # $\textit{rk}_1 \gets (N_1, H_6(K_1 || \textit{id}_2 || \textit{id}_3 || N_1) \cdot \textit{dk}_{\textit{id}_2, 2})$
		rk_2 = (N2, H6(self.__group.serialize(K2) + id_2 + id_3 + N2) * dk_id_2[0]) # $\textit{rk}_2 \gets (N_2, H_6(K_2 || \textit{id}_2 || \textit{id}_3 || N_2) \cdot \textit{dk}_{\textit{id}_2, 1})$
		rk = (id_1, id_2, rk_1, rk_2) # $\textit{rk} \gets (\textit{id}_1, \textit{id}_2, \textit{rk}_1, \textit{rk}_2)$
		
		# Return #
		return rk # \textbf{return} $\textit{rk}$
	def ProxyEnc(self:object, reKey:tuple, cipherText:tuple) -> tuple|bool: # $\textbf{ProxyEnc}(\textit{ct}, \textit{rk}) \rightarrow \textit{CT}$
		# Check #
		if not self.__flag:
			print("ProxyEnc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ProxyEnc`` subsequently. ")
			self.Setup()
		id2Generated = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
		if isinstance(reKey, tuple) and len(reKey) == 4 and all(isinstance(ele, bytes) for ele in reKey[:2]) and all(isinstance(ele, tuple) for ele in reKey[-2:]): # hybrid check
			rk, id2Generated = reKey, reKey[1]
		else:
			rk = self.PKGen(																														\
				self.SKGen(id2Generated), self.RKGen(id2Generated), randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), 	\
				id2Generated, randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")										\
			)
			print("ProxyEnc: The variable $\\textit{rk}$ should be a tuple containing 2 ``bytes`` object and 2 tuples but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and all(isinstance(ele, Element) for ele in cipherText[:3]) and isinstance(cipherText[3], int) and isinstance(cipherText[4], Element): # hybrid check
			C = cipherText
		else:
			C = self.Enc(self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), id2Generated, int.from_bytes(b"SchemePBAC", byteorder = "big"))
			print("ProxyEnc: The variable $C$ should be a tuple containing 4 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemePBAC\". ")
		del id2Generated
		
		# Unpack #
		g, H1, H5 = self.__mpk[0], self.__mpk[2], self.__mpk[6]
		id_1, id_2, rk_1, rk_2 = rk
		C1, C2, C3, C4, S = C
		
		# Scheme #
		h = H5(id_2 + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + C4.to_bytes(ceil(log(C4 + 1, 256)), byteorder = "big")) # $h \gets H_5(\textit{id}_2 || C_1 || C_2 || C_3 || C_4)$
		if pair(h, C1) == pair(g, S): # \textbf{if} $e(h, C_1) = e(g, S) $\textbf{then}
			t = self.__group.random(ZR) # generate $t \in \mathbb{Z}_r$ randomly
			C2Prime = C2 / (pair(C1, rk_1[1] * h ** t) / pair(g ** t, S)) # $C_2' \gets C_2 / \cfrac{e(C_1, \textit{rk}_{1, 2} \cdot h^t)}{e(g^t, S)}$
			C3Prime = C3 / pair(H1(id_1), rk_2[1]) # $C_3' \gets C_3 / e(H_1(\textit{id}_1), \textit{rk}_{2, 2})$
			CT = (id_1, C1, C2Prime, C3Prime, C4, rk_1[0], rk_2[0]) # $\textit{CT} \gets (\textit{id}_1, C_1, C_2', C_3', C_4, \textit{rk}_{1, 1}, \textit{rk}_{2, 1})$
		else: # \textbf{else}
			CT = False # \quad$\textit{CT} \gets \perp$
		# \textbf{end if}
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Dec1(self:object, dkid2:tuple, id2:bytes, id1:bytes, cipherText:tuple) -> int|bool: # $\textbf{Dec}_1(\textit{dk}_{\textit{id}_2}, \textit{id}_2, \textit{id}_1, \textit{ct}) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec1`` subsequently. ")
			self.Setup()
		if isinstance(id2, bytes): # type check:
			id_2 = id2
			if isinstance(dkid2, tuple) and len(dkid2) == 2 and all(isinstance(ele, Element) for ele in dkid2): # hybrid check
				dk_id_2 = dkid2
			else:
				dk_id_2 = self.RKGen(id_2)
				print("Dec1: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated accordingly. ")
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec1: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			dk_id_2 = self.RKGen(id_2)
			print("Dec1: The variable $\\textit{dk}_{\\textit{id}_2}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec1: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and all(isinstance(ele, Element) for ele in cipherText[:3]) and isinstance(cipherText[3], int) and isinstance(cipherText[4], Element): # hybrid check
			C = cipherText
		else:
			C = self.Enc(self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), id_2, int.from_bytes(b"SchemePBAC", byteorder = "big"))
			print("Dec1: The variable $C$ should be a tuple containing 4 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemePBAC\". ")
		
		# Unpack #
		g, H1, H3, H4, H5 = self.__mpk[0], self.__mpk[2], self.__mpk[4], self.__mpk[5], self.__mpk[6]
		C1, C2, C3, C4, S = C
		
		# Scheme #
		h = H5(id_2 + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + C4.to_bytes(ceil(log(C4 + 1, 256)), byteorder = "big")) # $h \gets H_5(\textit{id}_2 || C_1 || C_2 || C_3 || C_4)$
		t = self.__group.random(ZR) # generate $t \in \mathbb{Z}_r$ randomly
		eta_1 = C2 / (pair(C1, dk_id_2[1] * h ** t) / pair(g ** t, S)) # $\eta_1 \gets C_2 / \cfrac{e(C_1, \textit{dk}_{\textit{id}_2, 2} \cdot h^t)}{e(g^t, S)}$
		eta_2 = C3 / pair(dk_id_2[0], H1(id_1)) # $\eta_2 \gets C_3 / e(\textit{dk}_{\textit{id}_2, 1}, H_1(\textit{id}_1))$
		m = C4 ^ H4(eta_1) ^ H4(eta_2) # $m \gets C_4 \oplus H_4(\eta_1) \oplus H_4(\eta_2)$
		r = H3(eta_1, eta_2, m) # $r \gets H_3(\eta_1, \eta_2, m)$
		if S != h ** r or C1 != g ** r: # \textbf{if} $S \neq h^r \lor C_1 \neq g^r$ \textbf{then}
			m = False # \quad$m \gets \perp$
		# \textbf{end if}
		
		# Return #
		return m # \textbf{return} $m$
	def Dec2(self:object, dkid3:tuple, id3:bytes, id2:bytes, cipherText:tuple|bool) -> int|bool: # $\textbf{Dec}_2(\textit{dk}_{\textit{id}_3}, \textit{id}_3, \textit{id}_2, \textit{CT}) \rightarrow m'$
		# Check #
		if not self.__flag:
			print("Dec2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec2`` subsequently. ")
			self.Setup()
		if isinstance(id3, bytes): # type check
			id_3 = id3
			if isinstance(dkid3, tuple) and len(dkid3) == 2 and all(isinstance(ele, Element) for ele in dkid3): # hybrid check
				dk_id_3 = dkid3
			else:
				dk_id_3 = self.RKGen(id_3)
				print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		else:
			id_3 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_3$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			dk_id_3 = self.RKGen(id_3)
			print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ has been generated accordingly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if (																																\
			isinstance(cipherText, tuple) and len(cipherText) == 7 and isinstance(cipherText[0], bytes) and all(isinstance(ele, Element) for ele in cipherText[1:4])		\
			and isinstance(cipherText[4], int) and isinstance(cipherText[5], bytes) and isinstance(cipherText[6], bytes)										\
		): # hybrid check
			CT = cipherText
		elif isinstance(cipherText, bool):
			return False
		else:
			CT = self.ProxyEnc(self.PKGen(self.SKGen(id_2), self.RKGen(id_2), id_1, id_2, id_3), self.Enc(self.SKGen(id_1), id_2, b"SchemePBAC"))
			print("Dec2: The variable $\\textit{CT}$ should be a tuple containing 7 objects but it is not, which has been generated with $m$ set to b\"SchemePBAC\". ")
		
		# Unpack #
		g, H1, H2, H3, H4, H6 = self.__mpk[0], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[7]
		id_1, C1, C2Prime, C3Prime, C4, N1, N2 = CT
		
		# Scheme #
		K1Prime = pair(dk_id_3[1], H2(id_2)) # $K_1' \gets e(\textit{dk}_{\textit{id}_3, 2}, H_2(\textit{id}_2))$
		K2Prime = pair(dk_id_3[0], H1(id_2)) # $K_2' \gets e(\textit{dk}_{\textit{id}_3, 1}, H_1(\textit{id}_2))$
		eta1Prime = C2Prime * pair(C1, H6(self.__group.serialize(K1Prime) + id_2 + id_3 + N1)) # $\eta_1' \gets C_2' \cdot e(C_1, H_6(K_1' || \textit{id}_2 || \textit{id}_3 || N_1))$
		eta2Prime = C3Prime * pair(H6(self.__group.serialize(K2Prime) + id_2 + id_3 + N2), H1(id_1)) # $\eta_2' \gets C_3' \cdot e(H_6(K_2' || \textit{id}_2 || \textit{id}_3 || N_2), H_1(\textit{id}_1))$
		mPrime = C4 ^ H4(eta1Prime) ^ H4(eta2Prime) # $m' \gets C_4 \oplus H_4(\eta_1') \oplus H_4(\eta_2')$
		rPrime = H3(eta1Prime, eta2Prime, mPrime) # $r' \gets H_3(\eta_1', \eta_2', m')$
		if C1 != g ** rPrime: # \textbf{if} $C_1 \neq g^{r'}$ \textbf{then}
			mPrime = False # \quad$m' \gets \perp$
		# \textbf{end if}
		
		# Return #
		return mPrime # \textbf{return} $m'$
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


def Scheme(curveType:tuple|list|str, round:int|None = None) -> list:
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
		else:
			print("curveType = Unknown")
		if isinstance(round, int) and round >= 0:
			print("round =", round)
		print("Is the system valid? No. \n\t{0}".format(e))
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [round if isinstance(round, int) else None] + [False] * 4 + [-1] * 20																																	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemePBAC = SchemePBAC(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemePBAC.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# SKGen #
	startTime = perf_counter()
	id_1 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	id_2 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	ek_id_1 = schemePBAC.SKGen(id_1)
	ek_id_2 = schemePBAC.SKGen(id_2)
	endTime = perf_counter()
	timeRecords.append((endTime - startTime) / 2)
	
	# RKGen #
	startTime = perf_counter()
	id_3 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	dk_id_2 = schemePBAC.RKGen(id_2)
	dk_id_3 = schemePBAC.RKGen(id_3)
	endTime = perf_counter()
	timeRecords.append((endTime - startTime) / 2)
	
	# Enc #
	startTime = perf_counter()
	message = int.from_bytes(b"SchemePBAC", byteorder = "big")
	C = schemePBAC.Enc(ek_id_1, id_2, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# PKGen #
	startTime = perf_counter()
	rk = schemePBAC.PKGen(ek_id_2, dk_id_2, id_1, id_2, id_3)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# ProxyEnc #
	startTime = perf_counter()
	CT = schemePBAC.ProxyEnc(rk, C)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec1 #
	startTime = perf_counter()
	m = schemePBAC.Dec1(dk_id_2, id_2, id_1, C)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec2 #
	startTime = perf_counter()
	mPrime = schemePBAC.Dec2(dk_id_3, id_3, id_2, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(CT, bool), not isinstance(m, bool) and message == m, not isinstance(mPrime, bool) and message == mPrime]
	spaceRecords = [																																	\
		schemePBAC.getLengthOf(group.random(ZR)), schemePBAC.getLengthOf(group.random(G1)), schemePBAC.getLengthOf(group.random(GT)), 						\
		schemePBAC.getLengthOf(mpk), schemePBAC.getLengthOf(msk), schemePBAC.getLengthOf(ek_id_1), schemePBAC.getLengthOf(ek_id_2), 						\
		schemePBAC.getLengthOf(dk_id_2), schemePBAC.getLengthOf(dk_id_3), schemePBAC.getLengthOf(C), schemePBAC.getLengthOf(rk), schemePBAC.getLengthOf(CT)	\
	]
	del schemePBAC
	print("Original:", message)
	print("Dec1:", m)
	print("Dec2:", mPrime)
	print("Is ``ProxyEnc`` passed? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Is ``Dec1`` passed (m == message)? {0}. ".format("Yes" if booleans[2] else "No"))
	print("Is ``Dec2`` passed (m\' == message)? {0}. ".format("Yes" if booleans[3] else "No"))
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
	roundCount, filePath = 100, "SchemePBAC.xlsx"
	queries = ["curveType", "secparam", "roundCount"]
	validators = ["isSystemValid", "isProxyEncPassed", "isDec1Passed", "isDec2Passed"]
	metrics = 	[																						\
		"Setup (s)", "SKGen (s)", "RKGen (s)", "Enc (s)", "PKGen (s)", "ProxyEnc (s)", "Dec1 (s)", "Dec2 (s)", 			\
		"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 										\
		"mpk (B)", "msk (B)", "ek_id_1 (B)", "ek_id_2 (B)", "dk_id_2 (B)", "dk_id_3 (B)", "C (B)", "rk (B)", "CT (B)"	\
	]
	
	# Scheme #
	qLength, columns, results = len(queries), queries + validators + metrics, []
	length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
	try:
		for curveType in curveTypes:
			average = Scheme(curveType, round = 0)
			for round in range(1, roundCount):
				result = Scheme(curveType, round = round)
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