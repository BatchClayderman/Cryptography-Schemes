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


class SchemeIBPME:
	def __init__(self, group:None|PairingGroup = None) -> object: # This scheme is only applicable to symmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def Setup(self:object) -> tuple: # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Scheme #
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		h = self.__group.random(G1) # generate $h \in \mathbb{G}_1$ randomly
		x, alpha = self.__group.random(ZR), self.__group.random(ZR) # generate $x, \alpha \in \mathbb{Z}_r$ randomly
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, G1) # $H_2: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H3 = lambda x:self.__group.hash(x, ZR) # $H_3: \{0, 1\}^* \rightarrow \mathbb{Z}_r$
		H4 = lambda x:self.__group.hash(x, G1) # $H_4: \{0, 1\}^* \rightarrow \mathbb{G}_1^2$
		H5 = lambda x:self.__group.hash(x, G1) # $H_5: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H6 = lambda x:self.__group.hash(x, G1) # $H_6: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H7 = lambda x:self.__group.hash(x, G1) # $H_7: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		y = g ** x # $y \gets g^x$
		self.__mpk = (g, h, H1, H2, H3, H4, H5, H6, H7, y) # $ \textit{mpk} \gets (G, G_T, q, g, e, h, H_1, H_2, H_3, H_4, H_5, H_6, H_7, y)$
		self.__msk = (x, alpha) # $\textit{msk} \gets (x, \alpha)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # $\textbf{return }(\textit{mpk}, \textit{msk})$
	def DKGen(self:object, idR:bytes) -> tuple: # $\textbf{DKGen}(\textit{id}_R) \rightarrow \textit{dk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, bytes): # type check
			id_R = idR
		else:
			id_R = randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam >> 3) + (self.__group.secparam >> 3 << 3 != self.__group.secparam), byteorder = "big")
			print("DKGen: The variable $\\textit{id}_R$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[2]
		x, alpha = self.__msk
		
		# Scheme #
		dk_id_R1 = H1(id_R) ** x # $\textit{dk}_{\textit{id}_R, 1} \gets H_1(\textit{id}_R)^x$
		dk_id_R2 = H1(id_R) ** alpha # $\textit{dk}_{\textit{id}_R, 1} \gets H_1(\textit{id}_R)^\alpha$
		dk_id_R = (dk_id_R1, dk_id_R2) # $\textit{dk}_{\textit{id}_R} \gets (\textit{dk}_{\textit{id}_R, 1}, \textit{dk}_{\textit{id}_R, 2})$
		
		# Return #
		return dk_id_R # $\textbf{return }\textit{dk}_{\textit{id}_R}$
	def EKGen(self:object, idS:bytes) -> Element: # $\textbf{EKGen}(\textit{id}_S) \rightarrow \textit{ek}_{\textit{id}_S}$
		# Check #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(idS, bytes): # type check
			id_S = idS
		else:
			id_S = randbelow(1 << self.__group.secparam).to_bytes((self.__group.secparam >> 3) + (self.__group.secparam >> 3 << 3 != self.__group.secparam), byteorder = "big")
			print("EKGen: The variable $\\textit{id}_S$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H2 = self.__mpk[3]
		alpha = self.__msk[-1]
		
		# Scheme #
		ek_id_S = H2(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_2(\textit{id}_S)^\alpha$
		
		# Return #
		return ek_id_S # $\textbf{return }\textit{ek}_{\textit{id}_S}$
	def ReEKGen(self:object, ekid2:Element, dkid2:tuple, id1:bytes, id2:bytes, id3:bytes) -> tuple: # $\textbf{ReEKGen}(\textit{ek}_{\textit{id}_2}, \textit{dk}_{\textit{id}_2}, \textit{id}_1, \textit{id}_2, \textit{id}_3) \rightarrow \textit{rk}$
		# Check #
		if not self.__flag:
			print("ReEKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ReEKGen`` subsequently. ")
			self.Setup()
		if isinstance(id2, bytes): # type check:
			id_2 = id2
			if isinstance(ekid2, Element): # type check
				ek_id_2 = ekid2
			else:
				ek_id_2 = self.EKGen(id_2)
				print("ReEKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ should be an element but it is not, which has been generated accordingly. ")
			if isinstance(dkid2, tuple) and len(dkid2) == 2 and all([isinstance(ele, Element) for ele in dkid2]): # hybrid check
				dk_id_2 = dkid2
			else:
				dk_id_2 = self.DKGen(id_2)
				print("ReEKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated accordingly. ")
		else:
			id_2 = self.__group.random(ZR)
			print("ReEKGen: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			ek_id_2 = self.EKGen(id_2)
			print("ReEKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ has been generated accordingly. ")
			dk_id_2 = self.DKGen(id_2)
			print("ReEKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = self.__group.random(ZR)
			print("ReEKGen: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(id3, bytes): # type check
			id_3 = id3
		else:
			id_3 = self.__group.random(ZR)
			print("ReEKGen: The variable $\\textit{id}_3$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, h, H1, H2, H6, H7, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[7], self.__mpk[8], self.__mpk[-1]
		
		# Scheme #
		N = self.__group.random(ZR) # generate $N \in \{0, 1\}^\lambda$ randomly
		xBar = self.__group.random(ZR) # generate $\bar{x} \in \mathbb{Z}_r$ randomly
		rk1 = g ** xBar # $\textit{rk}_1 \gets g^{\bar{x}}$
		rk2 = dk_id_2[0] * h ** xBar * H6(pair(y, H1(id_3)) ** xBar) # $\textit{rk}_2 \gets \textit{dk}_{\textit{id}_2, 1} h^{\bar{x}} H_6(e(y, H_1(\textit{id}_3))^{\bar{x}})$
		K = pair(ek_id_2, H1(id_3)) # $K \gets e(\textit{ek}_{\textit{id}_2}, H_1(\textit{id}_3))$
		rk3 = pair( # $\textit{rk}_3 \gets e(
			H2(id_1), # H_2(\textit{id}_1), 
			H7(self.__group.serialize(K)[2:] + id_2 + id_3 + self.__group.serialize(N)[2:]) * dk_id_2[1] # H_7(K || \textit{id}_2 || \textit{id}_3 || N) \cdot \textit{dk}_{\textit{id}_2, 2}
		) # )$
		rk = (N, rk1, rk2, rk3) # $\textit{rk} \gets (N, \textit{rk}_1, \textit{rk}_2, \textit{rk}_3)$
		
		# Return #
		return rk # $\textbf{return }\textit{rk}$
	def Enc(self:object, ekid1:Element, id2:Element, message:Element) -> object: # $\textbf{Enc}(\textit{ek}_{\textit{id}_1}, \textit{id}_2, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(ekid1, Element): # type check
			ek_id_1 = ekid1
		else:
			ek_id_1 = self.EKGen(self.__group.random(ZR))
			print("Enc: The variable $\\textit{ek}_{\\textit{id}_1}$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = self.__group.random(ZR)
			print("Enc: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			m = message
		else:
			m = self.__group.random(GT)
			print("Enc: The variable $M$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, h, H1, H3, H4, H5, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[-1]
		
		# Scheme #
		sigma = self.__group.random(G1) # generate $\sigma \in \mathbb{G}_1$ randomly
		eta = self.__group.random(GT) # generate $\eta \in \mathbb{G}_T$ randomly
		r = H3(self.__group.serialize(m) + self.__group.serialize(sigma) + self.__group.serialize(eta)) # $r \gets H_3(m || \sigma || \eta)$
		ct1 = h ** r # $\textit{ct}_1 \gets h^r$
		ct2 = g ** r # $\textit{ct}_2 \gets g^r$
		ct3 = self.__group.init(
			ZR, (
				int.from_bytes(self.__group.serialize(m)[2:] + self.__group.serialize(sigma)[2:], byteorder = "big")
				^ int.from_bytes(self.__group.serialize(H4(pair(y, H1(id_2)) ** r))[2:], byteorder = "big")
				^ int.from_bytes(self.__group.serialize(H4(eta))[2:], byteorder = "big")
			)
		) # $\textit{ct}_3 \gets (m || \sigma) \oplus H_4(e(y, H_1(\textit{id}_2))^r) \oplus H_4(\eta)$
		ct4 = eta * pair(ek_id_1, H1(id_2)) # $\textit{ct}_4 \gets \eta \cdot e(\textit{ek}_{\textit{id}_1}, H_1(\textit{id}_2))$
		ct5 = H5(self.__group.serialize(ct1)[2:] + self.__group.serialize(ct2)[2:] + self.__group.serialize(ct3)[2:] + self.__group.serialize(ct4)[2:]) ** r # $\textit{ct}_5 \gets H_5(\textit{ct}_1 || \textit{ct}_2 || \textit{ct}_3 || \textit{ct}_4)^r$
		ct = (ct1, ct2, ct3, ct4, ct5) # $\textit{ct} \gets (\textit{ct}_1, \textit{ct}_2, \textit{ct}_3, \textit{ct}_4, \textit{ct}_5)$
		
		# Return #
		return ct # $\textbf{return }\textit{ct}$
	def ReEnc(self:object, cipher:tuple, reKey:tuple) -> tuple|bool: # $\textbf{ReEnc}(\textit{ct}, \textit{rk}) \rightarrow \textit{ct}'$
		# Check #
		if not self.__flag:
			print("ReEnc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ReEnc`` subsequently. ")
			self.Setup()
		id2Generated = self.__group.random(ZR)
		if isinstance(cipher, tuple) and len(cipher) == 5 and all([isinstance(ele, Element) for ele in cipher]): # hybrid check
			ct = cipher
		else:
			ct = self.Enc(self.EKGen(self.__group.random(ZR)), id2Generated, self.__group.random(GT))
			print("ReEnc: The variable $\\textit{ct}$ should be a tuple containing 5 elements but it is not, which has been generated randomly. ")
		if isinstance(reKey, tuple) and len(reKey) == 4 and all([isinstance(ele, Element) for ele in reKey]): # hybrid check
			rk = reKey
		else:
			rk = self.ReEKGen(self.EKGen(id2Generated), self.DKGen(id2Generated), self.__group.random(ZR), id2Generated, self.__group.random(ZR))
			print("ReEnc: The variable $\\textit{rk}$ should be a tuple containing 4 elements but it is not, which has been generated randomly. ")
		del id2Generated
		
		# Unpack #
		g, h, H1, H2, H5, H6, H7, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[-1]
		x = self.__msk[0]
		N, rk1, rk2, rk3 = rk
		ct1, ct2, ct3, ct4, ct5 = ct
		
		# Scheme #
		if (																															\
			pair(ct1, g) == pair(h, ct2)																									\
			and pair(ct1, H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + self.__group.serialize(ct3) + self.__group.serialize(ct4))) == pair(h, ct5)	\
		): # \textbf{If} $e(\textit{ct}_1, g) = e(h, \textit{ct}_2) \land e(\textit{ct}_1, H_5(\textit{ct}_1 || \textit{ct}_2 || \textit{ct}_3 || \textit{ct}_4)) = e(h, \textit{ct}_5)$ \textbf{then}
			ct4Prime = ct4 / rk3 # \quad$\textit{ct}_4' \gets \frac{\textit{ct}_4}{\textit{rk}_3}$
			ct6 = rk1 # $\textit{ct}_6 \gets \textit{rk}_1$
			ct7 = pair(rk2, ct2) / pair(ct1, rk1) # \quad$\textit{ct}_7 \gets \frac{e(\textit{rk}_2, \textit{ct}_2)}{e(\textit{ct}_1, \textit{rk}_1)}$
			ctPrime = (ct2, ct3, ct4Prime, ct6, ct7, N) # \quad$\textit{ct}' \gets (\textit{ct}_2, \textit{ct}_3, \textit{ct}_4', \textit{ct}_6, \textit{ct}_7, N)$
		else: # \textbf{else}
			ctPrime = False # \quad$\textit{ct}' \gets \perp$
		# \textbf{end if}
		
		# Return #
		return ctPrime # $\textbf{return }\textit{ct}'$
	def Dec1(self:object, dkid2:tuple, id1:Element, cipher:tuple) -> Element|bool: # $\textbf{Dec}_1(\textit{dk}_{\textit{id}_2}, \textit{id}_1, \textit{ct}) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec1`` subsequently. ")
			self.Setup()
		id2Generated = self.__group.random(ZR)
		if isinstance(dkid2, tuple) and len(dkid2) == 2 and all([isinstance(ele, Element) for ele in dkid2]): # hybrid check
			dk_id_2 = dkid2
		else:
			dk_id_2 = self.DKGen(id2Generated)
			print("Dec1: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = self.__group.random(ZR)
			print("Dec1: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 5 and all([isinstance(ele, Element) for ele in cipher]): # hybrid check
			ct = cipher
		else:
			ct = self.Enc(self.EKGen(self.__group.random(ZR)), id2Generated, self.__group.random(GT))
			print("Dec1: The variable $\\textit{ct}$ should be a tuple containing 5 elements but it is not, which has been generated randomly. ")
		del id2Generated
		
		# Unpack #
		g, h, H1, H2, H3, H4, H5, H6, H7, y = self.__mpk
		x = self.__msk[0]
		ct1, ct2, ct3, ct4, ct5 = ct
		
		# Scheme #
		if (																															\
			pair(ct1, g) == pair(h, ct2)																									\
			and pair(ct1, H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + self.__group.serialize(ct3) + self.__group.serialize(ct4))) == pair(h, ct5)	\
		): # If $e(\textit{ct}_1, g) = e(h, \textit{ct}_2) \land e(\textit{ct}_1, H_5(\textit{ct}_1 || \textit{ct}_2 || \textit{ct}_3 || \textit{ct}_4)) = e(h, \textit{ct}_5)$: 
			V = pair(dk_id_2[1], H2(id_1)) # \quad$V \gets e(\textit{dk}_{\textit{id}_2, 2}, H_2(\textit{id}_1))$
			etaPrime = ct4 / V # \quad$\eta' \gets \frac{\textit{ct}_4}{V}$
			r = H3(																									\
				(self.__group.serialize(ct3) ^ self.__group.serialize(H4(pair(dk_id_2[0], ct2))) ^ self.__group.serialize(H4(etaPrime)))		\
				+ self.__group.serialize(etaPrime)																			\
			) # \quad$r \gets H_3((\textit{ct}_3 \oplus H_4(e(\textit{dk}_{\textit{id}_2, 1})) \oplus H_4(\eta')) || \eta')$
			if g ** r == ct2: # \quad If $g^r = \textit{ct}_2$: 
				m = True
			else:
				m = False
		else:
			m = False
		
		# Return #
		return m # $\textbf{return }m$
	def Dec2(self:object, dkid3:tuple, id1:Element, id2:Element, id3:Element, cipherPrime:tuple|bool) -> Element|bool: # $\textbf{Dec}_2(\textit{dk}_{\textit{id}_3}, \textit{id}_1, \textit{id}_2, \textit{id}_3, \textit{ct}') \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec2`` subsequently. ")
			self.Setup()
		if isinstance(id3, bytes): # type check
			id_3 = id3
			if isinstance(dkid3, tuple) and len(dkid3) == 2 and all([isinstance(ele, Element) for ele in dkid3]): # hybrid check
				dk_id_3 = dkid3
			else:
				dk_id_3 = self.DKGen(id_3)
				print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		else:
			id_3 = self.__group.random(ZR)
			print("Dec2: The variable $\\textit{id}_3$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			dk_id_3 = self.DKGen(id_3)
			print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = self.__group.random(ZR)
			print("Dec2: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = self.__group.random(ZR)
			print("Dec2: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipherPrime, tuple) and len(cipherPrime) == 6 and all([isinstance(ele, Element) for ele in cipherPrime]): # hybrid check
			ctPrime = cipherPrime
		elif isinstance(cipherPrime, bool):
			return False
		else:
			ctPrime = self.ReEnc(self.Enc(self.EKGen(id_1), id_2, self.__group.random(GT)), self.ReEKGen(self.EKGen(id_2), self.DKGen(id_2), id_1, id_2, id_3))
			print("Dec2: The variable $\\textit{ct}'$ should be a tuple containing 6 elements but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, h, H1, H2, H3, H4, H6, H7, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[7], self.__mpk[8], self.__mpk[-1]
		x = self.__msk[0]
		ct2, ct3, ct4Prime, ct6, ct7, N = ctPrime
		
		# Scheme #
		V = pair(dk_id_3[1], H2(id_2)) # $V \gets e(\textit{dk}_{\textit{id}_3, 2}, H_2(\textit{id}_2))$
		etaPrime = ct4Prime * pair(H2(id_1), H7(self.__group.serialize(V) + self.__group.serialize(id2) + self.__group.serialize(id3) + self.__group.serialize(N))) # $\eta' \gets \textit{ct}_4' \cdot e(H_2(\textit{id}_1), H_7(V || \textit{id}_2 || \textit{id}_3 || N))$
		R = ct7 / pair(H6(pair(dk_id_3[0], ct6)), ct2) # $R \gets \frac{\textit{ct}_7}{e(H_6(e(\textit{dk}_{\textit{id}_3, 1}, \textit{ct}_6), \textit{ct}_2)}$
		r = H3(self.__group.serialize(ct3 ^ H4(R) ^ H4(etaPrime)) + self.__group.serialize(etaPrime)) # $r \gets H_3((\textit{ct}_3 \oplus H_4(R) \oplus H_4(\eta')) || \eta')$
		if g ** r == ct2: # If $g^r = \textit{ct}_2$: 
			m = True
		else:
			m = False
		
		# Return #
		return m # $\textbf{return }m$
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
	schemeIBPME = SchemeIBPME(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBPME.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DKGen #
	startTime = perf_counter()
	id_2 = randbelow(1 << group.secparam).to_bytes((group.secparam >> 3) + (group.secparam >> 3 << 3 != group.secparam), byteorder = "big")
	id_3 = randbelow(1 << group.secparam).to_bytes((group.secparam >> 3) + (group.secparam >> 3 << 3 != group.secparam), byteorder = "big")
	dk_id_2 = schemeIBPME.DKGen(id_2)
	dk_id_3 = schemeIBPME.DKGen(id_3)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# EKGen #
	startTime = perf_counter()
	id_1 = randbelow(1 << group.secparam).to_bytes((group.secparam >> 3) + (group.secparam >> 3 << 3 != group.secparam), byteorder = "big")
	ek_id_1 = schemeIBPME.EKGen(id_1)
	ek_id_2 = schemeIBPME.EKGen(id_2)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# ReEKGen #
	startTime = perf_counter()
	rk = schemeIBPME.ReEKGen(ek_id_2, dk_id_2, id_1, id_2, id_3)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = group.random(GT)
	ct = schemeIBPME.Enc(ek_id_1, id_2, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# ReEnc #
	startTime = perf_counter()
	ctPrime = schemeIBPME.ReEnc(ct, rk)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec1 #
	startTime = perf_counter()
	m = schemeIBPME.Dec1(dk_id_2, id_1, ct)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec2 #
	startTime = perf_counter()
	mPrime = schemeIBPME.Dec2(dk_id_3, id_1, id_2, id_3, ctPrime)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, isinstance(ctPrime, Element), isinstance(m, Element) and message == m, isinstance(mPrime, Element) and message == mPrime]
	spaceRecords = [																													\
		schemeIBPME.getLengthOf(group.random(ZR)), schemeIBPME.getLengthOf(group.random(G1)), 												\
		schemeIBPME.getLengthOf(group.random(G2)), schemeIBPME.getLengthOf(group.random(GT)), 											\
		schemeIBPME.getLengthOf(mpk), schemeIBPME.getLengthOf(msk), schemeIBPME.getLengthOf(ek_id_1), schemeIBPME.getLengthOf(ek_id_2), 		\
		schemeIBPME.getLengthOf(dk_id_2), schemeIBPME.getLengthOf(dk_id_3), schemeIBPME.getLengthOf(ct), schemeIBPME.getLengthOf(ctPrime)	\
	]
	del schemeIBPME
	print("Original:", message)
	print("Dec1:", m)
	print("Dec2:", mPrime)
	print("Is ``ReEnc`` passed? {0}. ".format("Yes" if booleans[1] else "No"))
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
	roundCount, filePath = 20, "SchemeIBPME.xlsx"
	columns = [																							\
		"curveType", "secparam", "roundCount", "isSystemValid", "isReEKGenPassed", "isDec1Passed", "isDec2Passed", 		\
		"Setup (s)", "DKGen (s)", "EKGen (s)", "ReEKGen (s)", "Enc (s)", "ReEnc (s)", "Dec1 (s)", "Dec2 (s)", 				\
		"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", "mpk (B)", "msk (B)", 			\
		"ek_id_1 (B)", "ek_id_2 (B)", "dk_id_2 (B)", "dk_id_3 (B)", "ct (B)", "ct\' (B)"									\
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