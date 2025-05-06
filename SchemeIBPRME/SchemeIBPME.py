import os
from sys import argv, exit
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
from math import ceil, log
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


class SchemeIBPME:
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def __hash(self:object, *objs:tuple, length:int|None = None) -> bytes:
		# bytes #
		bytesToBeHashed = b""
		for obj in objs:
			if isinstance(obj, Element):
				bytesToBeHashed += self.__group.serialize(obj)
			elif isinstance(obj, int):
				bytesToBeHashed += obj.to_bytes(ceil(log(obj + 1, 256)), byteorder = "big")
			elif isinstance(obj, bytes):
				bytesToBeHashed += obj
			else:
				try:
					bytesToBeHashed += bytes(obj)
				except:
					pass
		
		# length #
		length = length if isinstance(length, int) and length >= 1 else self.__group.secparam
		
		# convert #
		if 512 == length:
			return sha512(bytesToBeHashed).digest()
		elif 384 == length:
			return sha384(bytesToBeHashed).digest()
		elif 256 == length:
			return sha256(bytesToBeHashed).digest()
		elif 224 == length:
			return sha224(bytesToBeHashed).digest()
		elif 160 == length:
			return sha1(bytesToBeHashed).digest()
		elif 128 == length:
			return md5(bytesToBeHashed).digest()
		else:
			tmp = int.from_bytes(sha512(bytesToBeHashed).digest() * ceil(length / 512), byteorder = "big") & ((1 << length) - 1)
			return tmp.to_bytes(ceil(log(tmp + 1, 256)), byteorder = "big")
	def Setup(self:object) -> tuple: # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Scheme #
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		gHat = self.__group.init(G2, 1) # $\hat{g} \gets 1_{\mathbb{G}_2}$
		s, alpha, beta_0, beta_1 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $s, \alpha, \beta_0, \beta_1 \in \mathbb{Z}_r$ randomly
		g1 = g ** alpha # $g_1 \gets g^\alpha$
		f = g ** beta_0 # $f \gets g^{\beta_0}$
		fHat = gHat ** beta_0 # $\hat{f} \gets \hat{g}^{\beta_0}$
		h = g ** beta_1 # $h \gets g^{\beta_1}$
		hHat = gHat ** beta_1 # $\hat{h} \gets \hat{g}^{\beta_1}$
		H = lambda x:self.__group.hash(self.__group.serialize(x), ZR) # $H: \mathbb{G}_T \rightarrow \mathbb{Z}_r$
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, G2) # $H_2: \{0, 1\}^* \rightarrow \mathbb{G}_2$
		H3 = lambda x:self.__group.hash(self.__group.serialize(x), ZR) # $H_3: \mathbb{G}_T \rightarrow \mathbb{Z}_r$
		H4 = lambda x1, x2 = b"", x3 = b"":self.__hash(x1, x2, x3, self.__group.secparam) # $H_4: \{0, 1\}^\lambda \times \mathbb{G}_T^2 \times \mathbb{G}_1^2 \rightarrow \{0, 1\}^\lambda$
		if self.__group.secparam not in (128, 160, 224, 256, 384, 512):
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
		H5 = lambda x1, x2 = b"", x3 = b"", x4 = b"", x5 = b"":self.__hash(x1, x2, x3, x4, x5, self.__group.secparam) # $H_5: \{0, 1\}^\lambda \times \mathbb{G}_T^2 \times \mathbb{G}_1^2 \rightarrow \{0, 1\}^\lambda$
		H6 = lambda x:self.__hash(x, self.__group.secparam * 3) # $H_6: \mathbb{G}_T \rightarrow \{0, 1\}^{3\lambda}$
		H7 = lambda x:self.__hash(x, self.__group.secparam << 1) # $H_7: \mathbb{G}_T \rightarrow \{0, 1\}^{2\lambda}$
		self.__mpk = (g, gHat, g1, f, h, fHat, hHat, H, H1, H2, H3, H4, H5, H6, H7) # $ \textit{mpk} \gets (g, \hat{g}, g_1, f, h, \hat{f}, \hat{h}, H, H_1, H_2, H_3, H_4, H_5, H_6, H_7)$
		self.__msk = (s, alpha) # $\textit{msk} \gets (s, \alpha)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def SKGen(self:object, snd:bytes) -> Element: # $\textbf{SKGen}(\sigma) \rightarrow \textit{ek}_\sigma$
		# Check #
		if not self.__flag:
			print("SKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``SKGen`` subsequently. ")
			self.Setup()
		if isinstance(snd, bytes): # type check
			sigma = snd
		else:
			sigma = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("SKGen: The variable $\\sigma$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[8]
		s, alpha = self.__msk
		
		# Scheme #
		ek_sigma = H1(sigma) ** s # $\textit{ek}_\sigma \gets H_1(\sigma)^s$
		
		# Return #
		return ek_sigma # \textbf{return} $\textit{ek}_\sigma$
	def RKGen(self:object, rcv:bytes) -> tuple: # $\textbf{RKGen}(\rho) \rightarrow \textit{dk}_\rho$
		# Check #
		if not self.__flag:
			print("RKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``RKGen`` subsequently. ")
			self.Setup()
		if isinstance(rcv, bytes): # type check
			rho = rcv
		else:
			rho = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("RKGen: The variable $\\rho$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H2 = self.__mpk[9]
		s, alpha = self.__msk
		
		# Scheme #
		d1 = H2(rho) ** s # $d_1 \gets H_2(\rho)^s$
		d2 = H2(rho) ** alpha # $d_2 \gets H_2(\rho)^\alpha$
		dk_rho = (d1, d2) # $\textit{dk}_\rho \gets (d_1, d_2)$
		
		# Return #
		return dk_rho # \textbf{return} $\textit{dk}_\rho$
	def PKGen(self:object, dkrho:Element, snd:bytes) -> tuple: # $\textbf{PKGen}(\textit{dk}_\rho, \sigma) \rightarrow \textit{pdk}_{\rho, \sigma}$
		# Check #
		if not self.__flag:
			print("PKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``PKGen`` subsequently. ")
			self.Setup()
		if isinstance(dkrho, tuple) and len(dkrho) == 2 and all(isinstance(ele, Element) for ele in dkrho): # hybrid check
			dk_rho = dkrho
		else:
			dk_rho = self.RKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("PKGen: The variable $\\textit{dk}_\\rho$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(snd, bytes): # type check
			sigma = snd
		else:
			sigma = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("PKGen: The variable $\\sigma$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		gHat, fHat, hHat, H, H1, H3 = self.__mpk[1], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[10]
		d1, d2 = dk_rho
		
		# Scheme #
		y = self.__group.random(ZR) # generate $y \gets \mathbb{Z}_r$ randomly
		eta = pair(H1(sigma), d1) # $\eta \gets e(H_1(\sigma), d_1)$
		y1 = d2 ** H3(eta) * (fHat * hHat ** H(eta)) ** y # $y_1 \gets d_2^{H_3(\eta)}(\hat{f}\hat{h}^{H(\eta)})^y$
		y2 = gHat ** y # $y_2 \gets \hat{g}^y$
		pdk = (y1, y2) # $\textit{pdk}_{(\rho, \sigma)} \gets (y_1, y_2)$
		
		# Return #
		return pdk # \textbf{return} $\textit{pdk}_{(\rho, \sigma)}$
	def Enc(self:object, eksigma:Element, rcv:bytes, message:int|bytes) -> object: # $\textbf{Enc}(\textit{ek}_\sigma, \textit{id}_2, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(eksigma, Element): # type check
			ek_sigma = eksigma
		else:
			ek_sigma = self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("Enc: The variable $\\textit{ek}_\\sigma$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(rcv, bytes): # type check
			rho = rcv
		else:
			rho = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Enc: The variable $\\rho$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(message, int) and message >= 0: # type check
			m = message.to_bytes(ceil(log(message + 1, 256)), byteorder = "big")
		elif isinstance(message, bytes):
			m = message
		else:
			m = b"SchemeIBPME"
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemeIBPME\". ")
		
		# Unpack #
		g, g1, f, h, H, H2, H3, H4, H5, H6 = self.__mpk[0], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[7], self.__mpk[9], self.__mpk[10], self.__mpk[11], self.__mpk[12], self.__mpk[13]
		
		# Scheme #
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_r$ randomly
		eta = pair(ek_sigma, H2(rho)) # $\eta \gets e(\textit{ek}_\sigma, H_2(\rho))$
		K_R = pair(g1, H2(rho)) ** (r * H3(eta)) # $K_R \gets e(g_1, H_2(\rho))^{r \cdot H_3(\eta)}$
		C1 = g ** r # $C_1 \gets g^r$
		C2 = (f * h ** H(eta)) ** r # $C_2 \gets (fh^{H(\eta)})^r$
		K_C = H4(m, eta, K_R) # $K_C \gets H_4(m, \eta, K_R)$
		Y = H5(m, K_C, K_R, C1, C2) # $Y \gets H_5(m, K_C, K_R, C_1, C_2)$
		C3 = int.from_bytes(m + K_C + Y, byteorder = "big") ^ int.from_bytes(H6(K_R), byteorder = "big") # $C_3 \gets (m || K_C || Y) \oplus H_6(K_R)$
		C = (C1, C2, C3) # $C \gets (C_1, C_2, C_3)$
		
		# Return #
		return C # \textbf{return} $C$
	def ProxyDec(self:object, _pdk:tuple, cipher:tuple) -> tuple|bool: # $\textbf{ProxyDec}(\textit{pdk}, C) \rightarrow \textit{CT}$
		# Check #
		if not self.__flag:
			print("ProxyDec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ProxyDec`` subsequently. ")
			self.Setup()
		if isinstance(_pdk, tuple) and len(_pdk) == 2 and all(isinstance(ele, Element) for ele in _pdk): # hybrid check
			pdk = _pdk
		else:
			pdk = self.PKGen(																						\
				self.RKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), 		\
				randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")					\
			)
			print("ProxyDec: The variable $\\textit{pdk}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 3 and all(isinstance(ele, Element) for ele in cipher[:2]) and isinstance(cipher[2], int): # hybrid check
			C = cipher
		else:
			C = self.Enc(																								\
				self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), 			\
				randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), b"SchemeIBPME"		\
			)
			print("ProxyDec: The variable $C$ should be a tuple containing 2 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPME\". ")
		
		# Unpack #
		H5, H6, H7 = self.__mpk[12], self.__mpk[13], self.__mpk[14]
		y1, y2 = pdk
		C1, C2, C3 = C
		
		# Scheme #
		K_R = pair(C1, y1) / pair(C2, y2) # $K_R \gets e(C_1, y_1) / e(C_2, y_2)$
		m_KC_Y = C3 ^ int.from_bytes(H6(K_R), byteorder = "big") # $m || K_C || Y \gets C_3 \oplus H_6(K_R)$
		m_KC_Y = m_KC_Y.to_bytes(ceil(log(m_KC_Y + 1, 256)), byteorder = "big")
		m_KC, Y = m_KC_Y[:-ceil(self.__group.secparam / 8)], m_KC_Y[-ceil(self.__group.secparam / 8):]
		if Y == H5(m_KC, K_R, C1, C2): # \textbf{if} $Y = H_5(m, K_C, K_R, C_1, C_2) $\textbf{then}
			CT_1 = C1 # $\textit{CT}_1 \gets C_1$
			CT_2 = int.from_bytes(m_KC, byteorder = "big") ^ int.from_bytes(H7(K_R), byteorder = "big") # $\textit{CT}_2 \gets (m || K_C) \oplus H_7(K_R)$
			CT = (CT_1, CT_2) # $\textit{CT} \gets (\textit{CT}_1, \textit{CT}_2)$
		else: # \textbf{else}
			CT = False # \quad$\textit{CT} \gets \perp$
		# \textbf{end if}
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Dec1(self:object, dkrho:tuple, snd:bytes, cipher:tuple) -> Element|bool: # $\textbf{Dec}_1(\textit{dk}_\rho, \sigma, C) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec1`` subsequently. ")
			self.Setup()
		if isinstance(dkrho, tuple) and len(dkrho) == 2 and all(isinstance(ele, Element) for ele in dkrho): # hybrid check
			dk_rho = dkrho
		else:
			dk_rho = self.RKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("Dec1: The variable $\\textit{dk}_\\rho$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(snd, bytes): # type check
			sigma = snd
		else:
			sigma = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec1: The variable $\\sigma$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 3 and all(isinstance(ele, Element) for ele in cipher[:2]) and isinstance(cipher[2], int): # hybrid check
			C = cipher
		else:
			C = self.Enc(																								\
				self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), 			\
				randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), b"SchemeIBPME"		\
			)
			print("Dec1: The variable $C$ should be a tuple containing 2 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPME\". ")
		
		# Unpack #
		H1, H3, H4, H5, H6 = self.__mpk[8], self.__mpk[10], self.__mpk[11], self.__mpk[12], self.__mpk[13]
		d1, d2 = dk_rho
		C1, C2, C3 = C
		
		# Scheme #
		eta = pair(H1(sigma), d1) # $\eta \gets e(H_1(\sigma), d_1)$
		K_R = pair(C1, d2 ** H3(eta)) # $K_R \gets e(C_1, d_2^{H_3(\eta)})$
		m_KC_Y = C3 ^ int.from_bytes(H6(K_R), byteorder = "big") # $m || K_C || Y \gets C_3 \oplus H_6(K_R)$
		m_KC_Y = m_KC_Y.to_bytes(ceil(log(m_KC_Y + 1, 256)), byteorder = "big")
		m, K_C, Y = m_KC_Y[:-(ceil(self.__group.secparam / 8) << 1)], m_KC_Y[-(ceil(self.__group.secparam / 8) << 1):-ceil(self.__group.secparam / 8)], m_KC_Y[-ceil(self.__group.secparam / 8):]
		if K_C != H4(m, eta, K_R) or Y != H5(m, K_C, K_R, C1, C2): # \textbf{if} $K_C \neq H_4(m, \eta, K_R) \lor Y \neq H_5(m, K_C, K_R, C_1, C_2) $\textbf{then}
			m = False # \quad$m \gets \perp$
		# \textbf{end if}
		
		# Return #
		return m # \textbf{return} $m$
	def Dec2(self:object, dkrho:tuple, snd:bytes, cipherText:tuple) -> Element|bool: # $\textbf{Dec}_1(\textit{dk}_\rho, \sigma, \textit{CT}) \rightarrow m'$
		# Check #
		if not self.__flag:
			print("Dec2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec2`` subsequently. ")
			self.Setup()
		if isinstance(dkrho, tuple) and len(dkrho) == 2 and all(isinstance(ele, Element) for ele in dkrho): # hybrid check
			dk_rho = dkrho
		else:
			dk_rho = self.RKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("Dec2: The variable $\\textit{dk}_\\rho$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(snd, bytes): # type check
			sigma = snd
		else:
			sigma = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\sigma$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 2 and isinstance(cipherText[0], Element) and isinstance(cipherText[1], int): # hybrid check
			CT = cipherText
		elif isinstance(cipherText, bool):
			return False
		else:
			CT = self.ProxyDec(																							\
				self.PKGen(																								\
					self.RKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), 			\
					randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")						\
				), self.Enc(																								\
					self.SKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), 			\
					randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), b"SchemeIBPME"		\
				)																										\
			)
			print("Dec2: The variable $\\textit{CT}$ should be a tuple containing an element and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPME\". ")
		
		# Unpack #
		H1, H3, H4, H7 = self.__mpk[8], self.__mpk[10], self.__mpk[11], self.__mpk[14]
		d1, d2 = dk_rho
		CT_1, CT_2 = CT
		
		# Scheme #
		eta = pair(H1(sigma), d1) # $\eta \gets e(H_1(\sigma), d_1)$
		K_R = pair(CT_1, d2 ** H3(eta)) # $K_R \gets e(C_1, d_2^{H_3(\eta)})$
		m_KC = CT_2 ^ int.from_bytes(H7(K_R), byteorder = "big") # $m || K_C \gets \textit{CT}_2 \oplus H_7(K_R)$
		m_KC = m_KC.to_bytes(ceil(log(m_KC + 1, 256)), byteorder = "big")
		m, K_C = m_KC[:-ceil(self.__group.secparam / 8)], m_KC[-ceil(self.__group.secparam / 8):]
		if K_C != H4(m, eta, K_R): # \textbf{if} $K_C \neq H_4(m, \eta, K_R) $\textbf{then}
			m = False # \quad$m \gets \perp$
		# \textbf{end if}
		
		# Return #
		return m # \textbf{return} $m$
	def getLengthOf(self:object, obj:Element|tuple|list|set|bytes|int) -> int:
		if isinstance(obj, Element):
			return len(self.__group.serialize(obj))
		elif isinstance(obj, (tuple, list, set)):
			sizes = tuple(self.getLengthOf(o) for o in obj)
			return -1 if -1 in sizes else sum(sizes)
		elif isinstance(obj, bytes):
			return len(obj)
		elif isinstance(obj, int):
			return ceil(ceil(log(obj + 1, 256)) / (self.__group.secparam >> 3)) * (self.__group.secparam >> 3)
		elif callable(obj):
			if self.__mpk and obj == self.__mpk[13]: # H6
				return (self.__group.secparam >> 3) * 3
			elif self.__mpk and obj == self.__mpk[14]: # H7
				return self.__group.secparam >> 2
			else:
				return self.__group.secparam >> 3
		else:
			return -1


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
	except BaseException as e:
		if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
			print("curveType =", curveType[0])
			if curveType[1] >= 1:
				print("secparam =", curveType[1])
		elif isinstance(curveType, str):
			print("curveType =", curveType)
		if isinstance(round, int) and round >= 0:
			print("round =", round)
		print("Is the system valid? No. \n\t{0}".format(e))
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [round if isinstance(round, int) else None] + [False] * 4 + [-1] * 19																																	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBPME = SchemeIBPME(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBPME.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# SKGen #
	startTime = perf_counter()
	sigma = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	ek_sigma = schemeIBPME.SKGen(sigma)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# RKGen #
	startTime = perf_counter()
	rho = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	dk_rho = schemeIBPME.RKGen(rho)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# PKGen #
	startTime = perf_counter()
	pdk = schemeIBPME.PKGen(dk_rho, sigma)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = b"SchemeIBPME"
	C = schemeIBPME.Enc(ek_sigma, rho, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
		
	# ProxyDec #
	startTime = perf_counter()
	CT = schemeIBPME.ProxyDec(pdk, C)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec1 #
	startTime = perf_counter()
	m = schemeIBPME.Dec1(dk_rho, sigma, C)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec2 #
	startTime = perf_counter()
	mPrime = schemeIBPME.Dec2(dk_rho, sigma, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(CT, bool), not isinstance(m, bool) and message == m, not isinstance(mPrime, bool) and message == mPrime]
	spaceRecords = [																															\
		schemeIBPME.getLengthOf(group.random(ZR)), schemeIBPME.getLengthOf(group.random(G1)), schemeIBPME.getLengthOf(group.random(G2)), 				\
		schemeIBPME.getLengthOf(group.random(GT)), schemeIBPME.getLengthOf(mpk), schemeIBPME.getLengthOf(msk), schemeIBPME.getLengthOf(ek_sigma), 	\
		schemeIBPME.getLengthOf(dk_rho), schemeIBPME.getLengthOf(pdk), schemeIBPME.getLengthOf(C), schemeIBPME.getLengthOf(CT)						\
	]
	del schemeIBPME
	print("Original:", message)
	print("Dec1:", m)
	print("Dec2:", mPrime)
	print("Is ``ProxyDec`` passed? {0}. ".format("Yes" if booleans[1] else "No"))
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
	curveTypes = ("MNT159", "MNT201", "MNT224", "BN254", ("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
	roundCount, filePath = 20, "SchemeIBPME.xlsx"
	columns = [																					\
		"curveType", "secparam", "roundCount", "isSystemValid", "isProxyDecPassed", "isDec1Passed", 			\
		"isDec2Passed", "Setup (s)", "SKGen (s)", "RKGen (s)", "PKGen (s)", "Enc (s)", "ProxyDec (s)", 			\
		"Dec1 (s)", "Dec2 (s)", "elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 	\
		"mpk (B)", "msk (B)", "ek_sigma (B)", "dk_rho (B)", "pdk (B)", "C (B)", "CT (B)"						\
	]
	
	# Scheme #
	length, results = len(columns), []
	try:
		roundCount = max(1, roundCount)
		for curveType in curveTypes:
			average = Scheme(curveType, 0)
			for round in range(1, roundCount):
				result = Scheme(curveType, round)
				for idx in range(3, 7):
					average[idx] += result[idx]
				for idx in range(7, length):
					average[idx] = -1 if average[idx] < 0 or result[idx] < 0 else average[idx] + result[idx]
			average[2] = roundCount
			for idx in range(7, length):
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