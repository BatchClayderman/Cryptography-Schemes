import os
from sys import exit, getsizeof
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
from time import time
try:
	from psutil import Process
except:
	print("Cannot compute the memory via ``psutil.Process``. ")
	print("Please try to install psutil via ``python -m pip install psutil`` or ``apt-get install python3-psutil``. ")
	print("Please press the enter key to exit. ")
	input()
	exit(-1)
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element
except:
	print("The environment of the ``charm`` library is not handled correctly. ")
	print("See https://blog.csdn.net/weixin_45726033/article/details/144254189 in Chinese sif necessary. ")
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


class SchemeHIBME:
	def __init__(self:object, group:None|PairingGroup = None) -> None:
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__operand = (1 << self.__group.secparam) - 1 # use to cast binary strings
		self.__l = 30
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
	def Setup(self:object, l:int = 30) -> tuple: # $\textbf{Setup}(l) \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		if isinstance(l, int) and l >= 3: # boundary check
			self.__l = l
		else:
			self.__l = 30
			print("Setup: The variable $l$ should be an integer not smaller than $3$ but it is not, which has been defaulted to $30$. ")
		
		# Scheme #
		g = self.__group.random(G1) # generate $g \in \mathbb{G}_1$ randomly
		alpha, b1, b2 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $\alpha, b_1, b_2 \in \mathbb{Z}_p^*$ randomly
		s, a = tuple(self.__group.random(ZR) for _ in range(self.__l)), tuple(self.__group.random(ZR) for _ in range(self.__l)) # generate $s_1, s_2, \cdots, s_l, a_1, a_2, \cdots, a_l \in \mathbb{Z}_p^*$ randomly
		g2, g3 = self.__group.random(G2), self.__group.random(G2) # generate $g_2, g_3 \in \mathbb{G}_2$ randomly
		h = tuple(self.__group.random(G2) for _ in range(self.__l)) # generate $h_1, h_2, \cdots, h_l \in \mathbb{G}_2$ randomly (Note that the indexes in implementations are 1 smaller than those in theory)
		H1 = lambda x:self.__group.hash(x, G1) # $H_1:\mathbb{Z}_p^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(self.__group.serialize(x), G2) # $H_2:\mathbb{Z}_p^* \rightarrow \mathbb{G}_2$
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
			print("Setup: An inregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
		g1 = g ** alpha # $g_1 \gets g^\alpha$
		A = pair(g1, g2) # $A \gets e(g_1, g_2)$
		gBar = g ** b1 # $\bar{g} \gets g^{b_1}$
		gTilde = g ** b2 # $\tilde{g} \gets g^{b_2}$
		g3Bar = g3 ** (1 / b1) # $\bar{g}_3 \gets g_3^{\frac{1}{b_1}}$
		g3Tilde = g3 ** (1 / b2) # $\tilde{g}_3 \gets g_3^{\frac{1}{b_2}}$
		self.__mpk = (g, g1, g2, g3, gBar, gTilde, g3Bar, g3Tilde) + h + (H1, H2, HHat, A) # $\textit{mpk} \gets (g, g_1, g_2, g_3, \bar{g}, \tilde{g}, \bar{g}_3, \tilde{g}_3, h_1, h_2, \cdots, h_l, H_1, H_2, \hat{H}, A)$
		self.__msk = (g2 ** alpha, b1, b2) + s + a # $\textit{msk} \gets (g_2^\alpha, b_1, b_2, s_1, s_2, \cdots, s_l, a_1, a_2, \cdots, a_l)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # $\textbf{return }(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, IDk:tuple) -> tuple: # $\textbf{EKGen}(\textit{ID}_k) \rightarrow \textit{ek}_{\textit{ID}_k}$
		# Check #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l and all([isinstance(ele, Element) for ele in IDk]): # hybrid check
			ID_k = IDk
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																\
				"EKGen: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements where the integer $k \\in [2, {0}]$ but it is not, "		\
				+ "which has been generated randomly with a length of ${1} - 1 = {0}$. ".format(self.__l - 1, self.__l)												\
			)
		
		# Unpack #
		H1 = self.__mpk[-4]
		s, a = self.__msk[3:-self.__l], self.__msk[-self.__l:]
		k = len(ID_k)
		
		# Scheme #
		Ak = self.__product(tuple(a[j] for j in range(k))) # $A_k = \prod\limits_{j = 1}^k a_j$
		ek1 = tuple(H1(ID_k[i]) ** (s[i] * Ak) for i in range(k)) # $\textit{ek}_{1, i} \gets H_1(I_i)^{s_i A_k}, \forall i \in \{1, 2, \cdots, k\}$
		ek2 = tuple(s[k + i] * Ak for i in range(self.__l - k)) # $\textit{ek}_{2, i} \gets s_{k + i}A_k, \forall i \in \{1, 2, \cdots, l - k\}$
		ek3 = tuple(a[i] for i in range(k, self.__l)) # $\textit{ek}_3 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		ek_ID_k = (ek1, ek2, ek3) # $\textit{ek}_{\textit{ID}_k} \gets (\textit{ek}_1, \textit{ek}_2, \textit{ek}_3)$
		
		# Return #
		return ek_ID_k # $\textbf{return }\textit{ek}_{\textit{ID}_k}$
	def DerivedEKGen(self:object, ekIDkMinus1:tuple, IDk:tuple) -> tuple: # $\textbf{DerivedEKGen}(\textit{ek}_{\textit{ID}_{k - 1}}, \textit{ID}_k) \rightarrow \textit{ek}_{\textit{ID}_k}$
		# Check #
		if not self.__flag:
			print("DerivedEKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DerivedEKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l and all([isinstance(ele, Element) for ele in IDk]): # hybrid check
			ID_k = IDk
			if (																																											\
				isinstance(ekIDkMinus1, tuple) and len(ekIDkMinus1) == 3 and isinstance(ekIDkMinus1[0], tuple) and len(ekIDkMinus1[0]) == len(ID_k) - 1 and all([isinstance(ele, Element) for ele in ekIDkMinus1[0]])		\
				and isinstance(ekIDkMinus1[1], tuple) and len(ekIDkMinus1[1]) == self.__l - len(ID_k) + 1 and all([isinstance(ele, Element) for ele in ekIDkMinus1[1]])												\
				and isinstance(ekIDkMinus1[2], tuple) and len(ekIDkMinus1[2]) == self.__l - len(ID_k) + 1 and all([isinstance(ele, Element) for ele in ekIDkMinus1[2]])												\
			): # hybrid check
				ek_ID_kMinus1 = ekIDkMinus1
			else:
				ek_ID_kMinus1 = self.EKGen(ID_k[:-1])
				print(																																											\
					(																																											\
						"DerivedEKGen: The variable $\\textit{{ek}}_{{\\textit{{ID}}_{{k - 1}}}}$ should be a tuple containing a tuple with $k - 1 = {0}$ element(s) and two tuples with $l - k + 1 = {1}$ element(s) but it is not, "		\
						+ "which has been generated accordingly. "																																		\
					).format(len(ID_k) - 1, self.__l - len(ID_k) + 1)																																		\
				)
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																			\
				(																																			\
					"DerivedEKGen: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements where the integer $k \\in [2, {0}]$ but it is not, "		\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																				\
				).format(self.__l - 1, self.__l)																														\
			)
			ek_ID_kMinus1 = self.EKGen(ID_k[:-1])
			print("DerivedEKGen: The variable $\\textit{ek}_{\\textit{ID}_{k - 1}}$ is generated accordingly. ")
		
		# Unpack #
		H1 = self.__mpk[-4]
		a = self.__msk[-self.__l:]
		k = len(ID_k)
		ek1Minus1, ek2Minus1, ek3Minus1 = ek_ID_kMinus1
		
		# Scheme #
		ek1 = tuple(ek1Minus1[i] ** a[k - 1] for i in range(k - 1)) # $\textit{ek}'_{1, i} \gets \textit{ek}_{1, i}^{a_k}, \forall i \in \{1, 2, \cdots, k - 1\}$
		ek2 = tuple(ek2Minus1[i] * a[k - 1] for i in range(1, self.__l - k + 1)) # $\textit{ek}'_{2, i} \gets \textit{ek}_{2, i} \cdot a_k, \forall i \in \{2, 3, \cdots, l - k + 1\}$
		ek1k = H1(ID_k[k - 1]) ** ek2Minus1[0] # $\textit{ek}'_{1, k} \gets H_1(I_k)^{\textit{ek}_{2, 1}}$
		ek1 = ek1 + (ek1k, ) # $\textit{ek}'_1 \gets \textit{ek}'_1 || \langle\textit{ek}'_{1, k}\rangle$
		ek3 = tuple(a[i] for i in range(k, self.__l)) # $\textit{ek}'_3 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		ek_ID_k = (ek1, ek2, ek3) # $\textit{ek}_{\textit{ID}_k} \gets (\textit{ek}'_1, \textit{ek}'_2, \textit{ek}'_3)$
		
		# Return #
		return ek_ID_k # $\textbf{return }\textit{ek}_{\textit{ID}_k}$
	def DKGen(self:object, IDk:tuple) -> tuple: # $\textbf{DKGen}(\textit{ID}_k) \rightarrow \textit{dk}_{\textit{ID}_k}$
		# Check #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l and all([isinstance(ele, Element) for ele in IDk]): # hybrid check
			ID_k = IDk
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																	\
				(																																	\
					"DKGen: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements where the integer $k \\in [2, {0}]$ but it is not, "		\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																		\
				).format(self.__l - 1, self.__l)																												\
			)
		
		# Unpack #
		g, g3Bar, g3Tilde, h, H1, H2 = self.__mpk[0], self.__mpk[6], self.__mpk[7], self.__mpk[8:-4], self.__mpk[-4], self.__mpk[-3]
		g2ToThePowerOfAlpha, b1, b2, s, a = self.__msk[0], self.__msk[1], self.__msk[2], self.__msk[3:-self.__l], self.__msk[-self.__l:]
		k = len(ID_k)
		
		# Scheme #
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_p^*$ randomly
		HI = self.__product(tuple(h[i] ** ID_k[i] for i in range(k))) # $\textit{HI} \gets h_1^{I_1} h_2^{I_2} \cdots h_k^{I_k}$
		a0 = g2ToThePowerOfAlpha ** (b1 ** (-1)) * HI ** (r / b1) * g3Bar ** r # $a_0 \gets g_2^{\frac{\alpha}{b_1}} \cdot \textit{HI}^{\frac{r}{b_1}} \cdot \bar{g}_3^r$
		a1 = g2ToThePowerOfAlpha ** (b2 ** (-1)) * HI ** (r / b2) * g3Tilde ** r # $a_1 \gets g_2^{\frac{\alpha}{b_2}} \cdot \textit{HI}^{\frac{r}{b_2}} \cdot \tilde{g}_3^r$
		Ak = self.__product(tuple(a[j] for j in range(k))) # $A_k \gets \prod\limits_{j = 1}^k a_j$
		dk1 = ( # $\textit{dk}_1 \gets (
			(a0, a1, g ** r) # a_0, a_1, g^r, 
			+ tuple(h[i] ** (r / b1) for i in range(k, self.__l)) # h_{k + 1}^{\frac{r}{b_1}}, h_{k + 2}^{\frac{r}{b_1}}, \cdots, h_l^{\frac{r}{b_1}}, 
			+ tuple(h[i] ** (r / b2) for i in range(k, self.__l)) # h_{k + 1}^{\frac{r}{b_2}}, h_{k + 2}^{\frac{r}{b_2}}, \cdots, h_l^{\frac{r}{b_2}}, 
			+ tuple(h[i] ** (b1 ** (-1)) for i in range(k, self.__l)) # h_{k + 1}^{b_1^{-1}}, h_{k + 2}^{b_1^{-1}}, \cdots, h_l^{b_1^{-1}}, 
			+ tuple(h[i] ** (b2 ** (-1)) for i in range(k, self.__l)) # h_{k + 1}^{b_2^{-1}}, h_{k + 2}^{b_2^{-1}}, \cdots, h_2^{b_1^{-1}}, 
			+ (HI ** (1 / b1), HI ** (1 / b2)) # \textit{HI}^{\frac{1}{b_1}}, \textit{HI}^{\frac{1}{b_2}}
		) # )$
		dk2 = tuple(H2(ID_k[i]) ** (s[i] * Ak) for i in range(k)) # $\textit{dk}_{2, i} \gets H_2(I_i)^{s_i A_k}, \forall i \in \{1, 2, \cdots, k\}$
		dk3 = tuple(s[k + i - 1] * Ak for i in range(self.__l - k)) # $\textit{dk}_{3, i} \gets s_{k + i}A_k, \forall i \in \{1, 2, \cdots, l - k\}$
		dk4 = tuple(a[i] for i in range(k, self.__l)) # $\textit{dk}_4 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		dk_ID_k = (dk1, dk2, dk3, dk4) # $\textit{dk}_{\textit{ID}_k} \gets (\textit{dk}_1, \textit{dk}_2, \textit{dk}_3, \textit{dk}_4)$
		
		# Return #
		return dk_ID_k # $\textbf{return }\textit{dk}_{\textit{ID}_k}$
	def DerivedDKGen(self:object, dkIDkMinus1:tuple, IDk:tuple) -> tuple: # $\textbf{DerivedDKGen}(\textit{dk}_{\textit{ID}_{k - 1}}, \textit{ID}_k) \rightarrow \textit{dk}_{\textit{ID}_k}$
		# Check #
		if not self.__flag:
			print("DerivedDKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DerivedDKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l and all([isinstance(ele, Element) for ele in IDk]): # hybrid check
			ID_k = IDk
			if (
				isinstance(dkIDkMinus1, tuple) and len(dkIDkMinus1) == 4 and isinstance(dkIDkMinus1[0], tuple) and len(dkIDkMinus1[0]) == ((self.__l - len(ID_k) + 1) << 2) + 5 and all([isinstance(ele, Element) for ele in dkIDkMinus1[0]])
				and isinstance(dkIDkMinus1[1], tuple) and len(dkIDkMinus1[1]) == len(ID_k) - 1 and all([isinstance(ele, Element) for ele in dkIDkMinus1[1]])
				and isinstance(dkIDkMinus1[2], tuple) and len(dkIDkMinus1[2]) == self.__l - len(ID_k) + 1 and all([isinstance(ele, Element) for ele in dkIDkMinus1[2]])
				and isinstance(dkIDkMinus1[3], tuple) and len(dkIDkMinus1[3]) == self.__l - len(ID_k) + 1 and all([isinstance(ele, Element) for ele in dkIDkMinus1[3]])
			): # hybrid check
				dk_ID_kMinus1 = dkIDkMinus1
			else:
				dk_ID_kMinus1 = self.DKGen(ID_k[:-1])
				print(																																		\
					(																																		\
						"DerivedDKGen: The variable $\\textit{{dk}}_{{\\textit{{ID}}_{{k - 1}}}}$ should be a tuple containing a tuple with $(l - k + 1) \\times 4 + 5 = {0}$ elements, "	\
						+ "a tuple with $k - 1 = {1}$ element(s), and two tuples with $l - k + 1 = {2}$ element(s) but it is not, which has been generated accordingly. "					\
					).format(((self.__l - len(ID_k) + 1) << 2) + 5, len(ID_k) - 1, self.__l - len(ID_k) + 1)																		\
				)
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																		\
				(																																		\
					"DerivedDKGen: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements where the integer $k \\in [2, {0}]$ but it is not, "	\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																			\
				).format(self.__l - 1, self.__l)																													\
			)
			dk_ID_kMinus1 = self.DKGen(ID_k[:-1])
			print("DerivedDKGen: The variable $\\textit{dk}_{\\textit{ID}_{k - 1}}$ is generated accordingly. ")
		
		# Unpack #
		g, g3Bar, g3Tilde, h, H1, H2 = self.__mpk[0], self.__mpk[6], self.__mpk[7], self.__mpk[8:-4], self.__mpk[-4], self.__mpk[-3]
		a = self.__msk[-self.__l:]
		k = len(ID_k)
		dk1Minus1, dk2Minus1, dk3Minus1, dk4Minus1 = dk_ID_kMinus1
		a0Minus1, a1Minus1, bMinus1 = dk1Minus1[0], dk1Minus1[1], dk1Minus1[2]
		lengthPerToken = self.__l - k + 1
		c0Minus1, c1Minus1, d0Minus1, d1Minus1 = dk1Minus1[3:3 + lengthPerToken], dk1Minus1[3 + lengthPerToken:3 + (lengthPerToken << 1)], dk1Minus1[-2 - (lengthPerToken << 1):-2 - lengthPerToken], dk1Minus1[-2 - lengthPerToken:-2]
		f0Minus1, f1Minus1 = dk1Minus1[-2], dk1Minus1[-1]
		
		# Scheme #
		t = self.__group.random(ZR) # generate $t \in \mathbb{Z}_p^*$ randomly
		a0 = a0Minus1 * c0Minus1[0] ** ID_k[0] * (f0Minus1 * d0Minus1[0] ** ID_k[k - 1] * g3Bar) ** t # $a'_0 \gets a_0 \cdot c_{0, k}^{I_k} \cdot (f_0 \cdot d_{0, k}^{I_k} \cdot \bar{g}_3)^t$
		a1 = a1Minus1 * c1Minus1[0] ** ID_k[0] * (f1Minus1 * d1Minus1[0] ** ID_k[k - 1] * g3Tilde) ** t # $a'_1 \gets a_1 \cdot c_{1, k}^{I_k} \cdot (f_1 \cdot d_{1, k}^{I_k} \cdot \tilde{g}_3)^t$
		dk2 = tuple(dk2Minus1[i] ** a[k - 1] for i in range(k - 1)) # $\textit{dk}'_{2, i} \gets \textit{dk}_{2, i}^{a_k}, \forall i \in \{1, 2, \cdots, k - 1\}$
		dk3 = tuple(dk3Minus1[i] ** a[k - 1] for i in range(1, self.__l - k + 1)) # $\textit{dk}'_{3, i} \gets \textit{dk}_{3, i} \cdot a_k, \forall i \{2, 3, \cdots, l - k + 1\}$
		dk2k = H2(ID_k[k - 1]) ** dk3[0] # $\textit{dk}'_{2, k} \gets H_2(I_k)^{\textit{dk}_{3, 1}}$
		dk2 = dk2 + (dk2k, ) # $\textit{dk}'_2 \gets \textit{dk}'_2 || \langle\textit{dk}'_{2, k}\rangle$
		dk1 = ( # $\textit{dk}'_1 \gets (
			(a0, a1, bMinus1 * g ** t) # a'_0, a'_1, b \cdot g^t, 
			+ tuple(c0Minus1[i] * d0Minus1[i] ** t for i in range(1, self.__l - k + 1)) # c_{0, k + 1} \cdot d_{0, k + 1}^t, c_{0, k + 2} \cdot d_{0, k + 2}^t, \cdots, c_{0, l} \cdot d_{0, l}^t, 
			+ tuple(c1Minus1[i] * d1Minus1[i] ** t for i in range(1, self.__l - k + 1)) # c_{1, k + 1} \cdot d_{1, k + 1}^t, c_{1, k + 2} \cdot d_{1, k + 2}^t, \cdots, c_{1, l} \cdot d_{1, l}^t, 
			+ tuple(d0Minus1[i] for i in range(1, self.__l - k + 1)) # d_{0, k + 1}, d_{0, k + 2}, \cdots, d_{0, l}, 
			+ tuple(d1Minus1[i] for i in range(1, self.__l - k + 1)) # d_{1, k + 1}, d_{1, k + 2}, \cdots, d_{1, l}, 
			+ (f0Minus1 * c0Minus1[0] ** ID_k[k - 1], f1Minus1 * c1Minus1[0] ** ID_k[k - 1]) # f_0 \cdot c_{0, k}^{I_k}, f_1 \cdot c_{1, k}^{I_k}
		) # )$
		dk4 = tuple(a[k + i] for i in range(self.__l - k)) # $\textit{dk}'_4 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		dk_ID_k = (dk1, dk2, dk3, dk4) # $\textit{dk}_{\textit{ID}_k} \gets (\textit{dk}'_1, \textit{dk}'_2, \textit{dk}'_3, \textit{dk}'_4)$
				
		# Return #
		return dk_ID_k # $\textbf{return }\textit{dk}_{\textit{ID}_k}$
	def Enc(self:object, ekIDS:tuple, IDSnd:tuple, IDRev:tuple, message:bytes|int) -> Element: # $\textbf{Enc}(\textit{ek}_{\textit{ID}_S}, \textit{ID}_\textit{Rev}, M) \rightarrow \textit{CT}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(IDSnd, tuple) and 2 <= len(IDSnd) < self.__l and all([isinstance(ele, Element) for ele in IDSnd]): # hybrid check
			ID_Snd = IDSnd
			if (
				isinstance(ekIDS, tuple) and len(ekIDS) == 3 and isinstance(ekIDS[0], tuple) and len(ekIDS[0]) == len(ID_Snd) and all([isinstance(ele, Element) for ele in ekIDS[0]])
				and isinstance(ekIDS[1], tuple) and len(ekIDS[1]) == self.__l - len(ID_Snd) and all([isinstance(ele, Element) for ele in ekIDS[1]])
				and isinstance(ekIDS[2], tuple) and len(ekIDS[2]) == self.__l - len(ID_Snd) and all([isinstance(ele, Element) for ele in ekIDS[2]])
			): # hybrid check
				ek_ID_S = ekIDS
			else:
				ek_ID_S = self.EKGen(ID_Snd)
				print(
					"Enc: The variable $\\textit{{ek}}_{{\\textit{{ID}}_S}}$ should be a tuple containing a tuple with $n = {0}$ elements and two tuples with $l - n = {1}$ element(s) but it is not, which has been generated accordingly. ".format(		\
						len(ID_Snd), self.__l - len(ID_Snd)																																							\
					)																																														\
				)
		else:
			ID_Snd = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																					\
				(																																					\
					"Enc: The variable $\\textit{{ID}}_\textit{{Snd}}$ should be a tuple containing $n = \\|\\textit{{ID}}_\\textit{{Snd}}\\|$ elements where the integer $n \\in [2, {0}]$ but it is not, "	\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																						\
				).format(self.__l - 1, self.__l)																																\
			)
			ek_ID_S = self.EKGen(ID_Snd)
			print("Enc: The variable $\\textit{ek}_{\\textit{ID}_S}$ is generated accordingly. ")
		if isinstance(IDRev, tuple) and 2 <= len(IDRev) < self.__l and all([isinstance(ele, Element) for ele in IDRev]): # hybrid check
			ID_Rev = IDRev
		else:
			ID_Rev = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																					\
				(																																					\
					"Enc: The variable $\\textit{{ID}}_\textit{{Rev}}$ should be a tuple containing $m = \\|\\textit{{ID}}_\\textit{{Rev}}\\|$ elements where the integer $m \\in [2, {0}]$ but it is not, "	\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																						\
				).format(self.__l - 1, self.__l)																																\
			)
		if isinstance(message, int): # type check
			M = message & self.__operand
			if message != M:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			M = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			M = int.from_bytes(b"SchemeHIBME", byteorder = "big") & self.__operand
			print("Enc: The message passed should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemeHIBME\". ")
		
		# Unpack #
		g, g3, gBar, gTilde, h, H1, H2, HHat, A = self.__mpk[0], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[8:-4], self.__mpk[-4], self.__mpk[-3], self.__mpk[-2], self.__mpk[-1]
		a = self.__msk[-self.__l:]
		n, m = len(ID_Snd), len(ID_Rev)
		
		# Scheme #
		s1, s2, eta = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $s_1, s_2, \eta \in \mathbb{Z}_p^*$ randomly
		T = A ** (s1 + s2) # $T \gets A^{s_1 + s_2}$
		if m == n: # If $m = n$:
			K = self.__product(tuple(pair(g ** eta * ek_ID_S[0][i], H2(ID_Rev[i])) for i in range(n))) # $K \gets \prod_{i = 1}^n e(g^{\eta} \cdot \textit{ek}_{1, i}, H_2(I'_i))$
		elif m > n: # If $m > n$:
			An = self.__product(tuple(a[i] for i in range(n))) # $A_n \gets \prod\limits_{i = 1}^n a_i$
			Bmn = self.__product(tuple(a[i] for i in range(n, m))) # $B_n^m \gets \prod\limits_{i = n + 1}^m a_i$
			K = ( # $K \gets
				( # (
					self.__product(tuple(pair(ek_ID_S[0][i], H2(ID_Rev[i])) for i in range(n))) # \prod\limits_{i = 1}^n e(\textit{ek}_{1, i}, H_2(I'_i))
					* self.__product(tuple(pair(H1(ID_Snd[n - 1]), H2(ID_Rev[i])) ** (a[i] * An) for i in range(n, m))) # \cdot \prod\limits_{i = n + 1}^m e(H_1(I_n), H_2(I'_i))^{\alpha_i A_n}
				) ** Bmn # )^{B_n^m}
				* pair(g ** eta, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # \cdot e(g^{\eta}, \prod\limits_{i = 1}^m H_2(I'_i))
			) # $
		else: # If $m < n$
			K = ( # $K \gets
				self.__product(tuple(pair(ek_ID_S[0][i], H2(ID_Rev[i])) for i in range(m))) # \prod\limits_{i = 1}^m e(\textit{ek}_{1, i}, H_2(I'_i))
				* self.__product(tuple(pair(ek_ID_S[0][i], H2(ID_Rev[m - 1])) for i in range(m, n))) # \prod\limits_{i = m + 1}^n e(\textit{ek}_{1, i}, H_2(I'_m))
				* pair(g ** eta, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # e(g^{\eta}, \prod\limits_{i = 1}^m H_2(I'_i))
			) # $
		C1 = M ^ HHat(T) ^ HHat(K) # $C_1 \gets M \oplus \hat{H}(T) \oplus \hat{H}(K)$
		C2 = gBar ** s1 # $C_2 \gets \bar{g}^{s_1}$
		C3 = gTilde ** s2 # $C_3 \gets \tilde{g}^{s_2}$
		C4 = (self.__product(tuple(h[i] ** ID_Snd[i] for i in range(n))) * g3) ** (s1 + s2) # $C_4 \gets (h_1^{I_1} h_2^{I_2} \cdots h_n^{I_n} \cdot g_3)^{s_1 + s_2}$
		C5 = g ** eta # $C_5 \gets g^{\eta}$
		CT = (C1, C2, C3, C4, C5) # $\textit{CT} \gets (C_1, C_2, C_3, C_4, C_5)$
		
		# Return #
		return CT # $\textbf{return }\textit{CT}$
	def Dec(self:object, dkIDR:tuple, IDRev:tuple, IDSnd:tuple, cipher:tuple) -> bytes: # $\textbf{Dec}(\textit{dk}_{\textit{ID}_R}, \textit{ID}_\textit{Rev}, \textit{ID}_\textit{Snd}, \textit{CT}) \rightarrow M$
		# Check #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if isinstance(IDRev, tuple) and 2 <= len(IDRev) < self.__l and all([isinstance(ele, Element) for ele in IDRev]): # hybrid check
			ID_Rev = IDRev
			if (
				isinstance(dkIDR, tuple) and len(dkIDR) == 4 and isinstance(dkIDR[0], tuple) and len(dkIDR[0]) == ((self.__l - len(ID_Rev)) << 2) + 5 and all([isinstance(ele, Element) for ele in dkIDR[0]])
				and isinstance(dkIDR[1], tuple) and len(dkIDR[1]) == len(ID_Rev) and all([isinstance(ele, Element) for ele in dkIDR[1]])
				and isinstance(dkIDR[2], tuple) and len(dkIDR[2]) == self.__l - len(ID_Rev) and all([isinstance(ele, Element) for ele in dkIDR[2]])
				and isinstance(dkIDR[3], tuple) and len(dkIDR[3]) == self.__l - len(ID_Rev) and all([isinstance(ele, Element) for ele in dkIDR[3]])
			): # hybrid check
				dk_ID_R = dkIDR
			else:
				dk_ID_R = self.DKGen(ID_Rev)
				print(																														\
					(																														\
						"Dec: The variable $\\textit{dk}_{\\textit{ID}_R}$ should be a tuple containing a tuple with $(l - m) \\times 4 + 5 = {0}$ elements, "			\
						+ "a tuple with $m - 1 = {1}$ element(s), and two tuples with $l - m = {2}$ element(s) but it is not, which has been generated accordingly. "		\
					).format(((self.__l - len(ID_Rev)) << 2) + 5, len(ID_Rev), self.__l - len(ID_Rev))														\
				)
		else:
			ID_Rev = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																						\
				(																																						\
					"Dec: The variable $\\textit{{ID}}_\\textit{{Rev}}$ should be a tuple containing $m = \\|\\textit{{ID}}_\\textit{{Rev}}\\|$ elements where the integer $m \\in [2, {0}]$ but it is not, "		\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																							\
				).format(self.__l - 1, self.__l)																																	\
			)
			dk_ID_R = self.DKGen(ID_Rev)
			print("Dec: The variable $\\textit{dk}_{\\textit{ID}_R}$ is generated accordingly. ")
		if isinstance(IDSnd, tuple) and 2 <= len(IDSnd) < self.__l and all([isinstance(ele, Element) for ele in IDSnd]): # hybrid check
			ID_Snd = IDSnd
		else:
			ID_Snd = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print(																																					\
				(																																					\
					"Dec: The variable $\\textit{{ID}}_\\textit{{Snd}}$ should be a tuple containing $n = \\|\\textit{{ID}}_\\textit{{Snd}}\\|$ elements where the integer $n \\in [2, {0}]$ but it is not, "	\
					+ "which has been generated randomly with a length of ${1} - 1 = {0}$. "																						\
				).format(self.__l - 1, self.__l)																																\
			)
		if isinstance(cipher, tuple) and len(cipher) == 5 and isinstance(cipher[0], int) and all([isinstance(ele, Element) for ele in cipher[1:]]): # hybrid check
			CT = cipher
		else:
			CT = self.Enc(self.EKGen(ID_Snd), ID_Snd, ID_Rev, b"SchemeHIBME")
			print("Dec: The variable $\\textit{CT}$ should be a tuple containing an integer and 4 elements but it is not, which has been generated with $M$ set to b\"SchemeHIBME\". ")
		
		# Unpack #
		H1, H2, HHat = self.__mpk[-4], self.__mpk[-3], self.__mpk[-2]
		a = self.__msk[-self.__l:]
		C1, C2, C3, C4, C5 = CT
		dk1, dk2, dk3, dk4 = dk_ID_R
		m, n = len(ID_Rev), len(ID_Snd)
		
		# Scheme #
		TPi = pair(dk1[2], C4) / (pair(C2, dk1[0]) * pair(C3, dk1[1])) # $T' = \cfrac{e(\textit{dk}_{1, 3}, C_4)}{e(C_2, \textit{dk}_{1, 1})e(C_3, \textit{dk}_{1, 2})}$
		if m == n: # If $m = n$:
			KPi = ( # $K' \gets
				self.__product(tuple(pair(H1(ID_Snd[i]), dk2[i]) for i in range(n))) # \prod\limits_{i = 1}^n e(H_1(I_i), \textit{dk}_{2, i}) 
				 * pair(C5, self.__product(tuple(H2(ID_Rev[i]) for i in range(n)))) # \cdot e(C_5, \prod\limits_{i = 1}^n H_2(I'_i))
			) # $
		elif m > n: # If $m > n$:
			KPi = ( # $K' \gets
				self.__product(tuple(pair(H1(ID_Snd[i]), dk2[i]) for i in range(n))) # \prod\limits_{i = 1}^n e(H_1(I_i), \textit{dk}_{2, i})
				* self.__product(tuple(pair(H1(ID_Snd[n - 1]), dk2[i]) for i in range(n, m))) # \cdot \prod\limits_{i = n + 1}^m e(H_1(I_n), \textit{dk}_{2, i})
				* pair(C5, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # \cdot e(C_5, \prod\limits_{i = 1}^m H_2(I'_i))
			) # $
		else: # If $m < n$
			Am = self.__product(tuple(a[i] for i in range(m))) # $A_m \gets \prod\limits_{i = 1}^m a_i$
			Bnm = self.__product(tuple(a[i] for i in range(m, n))) # $B_n^m \gets \prod\limits_{i = m + 1}^n a_i$
			KPi = ( # $K' \gets
				( # (
					self.__product(tuple(pair(H1(ID_Snd[i]), dk2[i]) for i in range(m))) # \prod\limits_{i = 1}^m e(H_1(I_i), \textit{dk}_{2, i})
					* self.__product(tuple(pair(H1(ID_Snd[i]), H2(ID_Rev[m - 1])) ** (a[i] * Am) for i in range(m, n))) # \cdot \prod\limits_{i = m + 1}^n e(H_1(I_i), H_2(I'_m))^{\alpha_i A_m}
				) ** Bnm # )^{B_m^n}
				* pair(C5, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # \cdot e(C_5, \prod\limits_{i = 1}^m H_2(I'_i))
			) # $
		M = C1 ^ HHat(TPi) ^ HHat(KPi) # $M \gets C_1 \oplus \hat{H}(T') \oplus \hat{H}(K')$
		
		# Return #
		return M # $\textbf{return }M$


def Scheme(curveType:tuple|list|str, l:int, m:int, n:int, round:int = None) -> list:
	# Begin #
	if isinstance(l, int) and isinstance(m, int) and isinstance(n, int) and 2 <= m < l and 2 <= n < l: # no need to check the parameters for curve types here
		try:
			if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
				if curveType[1] >= 1:
					group = PairingGroup(curveType[0], secparam = curveType[1])
				else:
					group = PairingGroup(curveType[0])
			else:
				group = PairingGroup(curveType)
		except:
			if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int):
				print("curveType =", curveType[0])
				if curveType[1] >= 1:
					print("secparam =", curveType[1])
			elif isinstance(curveType, str):
				print("curveType =", curveType)
			else:
				print("curveType = Unknown")
			print("l =", l)
			print("m =", m)
			print("n =", n)
			if isinstance(round, int) and round >= 0:
				print("Round =", round)
			print("Is the system valid? No. {0}. ".format(e))
			return (																																														\
				([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [(curveType if isinstance(curveType, str) else None), None])		\
				+ [l, m, n, round if isinstance(round, int) and round >= 0 else None] + [False] * 3 + [-1] * 19																												\
			)
	else:
		print("Is the system valid? No. The parameters $l$, $m$, and $n$ should be three positive integers satisfying $2 \\leqslant m < l \\land 2 \\leqslant n < l$. ")
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [(curveType if isinstance(curveType, str) else None), None])		\
			+ [l if isinstance(l, int) else None, m if isinstance(m, int) else None, n if isinstance(n, int) else None, round if isinstance(round, int) and round >= 0 else None] + [False] * 3 + [-1] * 19											\
		)
	process = Process(os.getpid())
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	print("l =", l)
	print("m =", m)
	print("n =", n)
	if isinstance(round, int) and round >= 0:
		print("Round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeHIBME = SchemeHIBME(group)
	timeRecords, memoryRecords = [], []
	
	# Setup #
	startTime = time()
	mpk, msk = schemeHIBME.Setup(l)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# EKGen #
	startTime = time()
	ID_Snd = tuple(group.random(ZR) for i in range(n))
	ek_ID_S = schemeHIBME.EKGen(ID_Snd)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# DerivedEKGen #
	startTime = time()
	ek_ID_SMinus1 = schemeHIBME.EKGen(ID_Snd[:-1]) # remove the last one to generate the ek_ID_SMinus1
	ek_ID_SDerived = schemeHIBME.DerivedEKGen(ek_ID_SMinus1, ID_Snd)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# DKGen #
	startTime = time()
	ID_Rev = tuple(group.random(ZR) for i in range(m))
	dk_ID_R = schemeHIBME.DKGen(ID_Rev)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# DerivedDKGen #
	startTime = time()
	dk_ID_RMinus1 = schemeHIBME.DKGen(ID_Rev[:-1]) # remove the last one to generate the dk_ID_RMinus1
	dk_ID_RDerived = schemeHIBME.DerivedDKGen(dk_ID_RMinus1, ID_Rev)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Enc #
	startTime = time()
	message = int.from_bytes(b"SchemeHIBME", byteorder = "big")
	CT = schemeHIBME.Enc(ek_ID_S, ID_Snd, ID_Rev, message)
	CTDerived = schemeHIBME.Enc(ek_ID_SDerived, ID_Snd, ID_Rev, message)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Dec #
	startTime = time()
	M = schemeHIBME.Dec(dk_ID_R, ID_Rev, ID_Snd, CT)
	MDerived = schemeHIBME.Dec(dk_ID_RDerived, ID_Rev, ID_Snd, CT)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# End #
	sizeRecords = [getsizeof(ek_ID_S), getsizeof(ek_ID_SDerived), getsizeof(dk_ID_R), getsizeof(dk_ID_RDerived), getsizeof(CT)]
	del schemeHIBME
	print("Original:", message)
	print("Derived:", MDerived)
	print("Decrypted:", M)
	print("Is the derver passed (message == M')? {0}. ".format("Yes" if message == MDerived else "No"))
	print("Is the scheme correct (message == M)? {0}. ".format("Yes" if message == M else "No"))
	print("Time:", timeRecords)
	print("Memory:", memoryRecords)
	print("Size:", sizeRecords)
	print()
	return [group.groupType(), group.secparam, l, m, n, round if isinstance(round, int) else None, True, message == MDerived, message == M] + timeRecords + memoryRecords + sizeRecords

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
	curveTypes = ("MNT159", "MNT201", "MNT224", ("SS512", 512))
	roundCount, filePath = 20, "SchemeHIBME.xlsx"
	columns = [																						\
		"curveType", "secparam", "l", "m", "n", "roundCount", "isSystemValid", "isDeriverPassed", "isSchemeCorrect", 	\
		"Setup (s)", "EKGen (s)", "DerivedEKGen (s)", "DKGen (s)", "DerivedDKGen (s)", "Enc (s)", "Dec (s)", 		\
		"Setup (B)", "EKGen (B)", "DerivedEKGen (B)", "DKGen (B)", "DerivedDKGen (B)", "Enc (B)", "Dec (B)", 	\
		"EK (B)", "EK' (B)", "DK (B)", "DK' (B)", "CT (B)"													\
	]
	
	# Scheme #
	length, results = len(columns), []
	try:
		roundCount = max(1, roundCount)
		for curveType in curveTypes:
			for l in (5, 10, 15, 20, 25, 30):
				for m in range(5, l, 5):
					for n in range(5, l, 5):
						average = Scheme(curveType, l, m, n, 0)
						for round in range(1, roundCount):
							result = Scheme(curveType, l, m, n, round)
							for idx in range(6, 9):
								average[idx] += result[idx]
							for idx in range(9, length):
								average[idx] = -1 if -1 == average[idx] or -1 == result[idx] else average[idx] + result[idx]
						average[5] = roundCount
						for idx in range(9, length):
							average[idx] = -1 if -1 == average[idx] else average[idx] / roundCount
						results.append(average)
	except KeyboardInterrupt:
		print("\nThe experiments were interrupted by users. The program will try to save the results collected. ")
	#except BaseException as e:
	#	print("The experiments were interrupted by the following exceptions. The program will try to save the results collected. \n\t{0}".format(e))
	
	# Output #
	print()
	if results:
		if handleFolder(os.path.split(filePath)[0]):
			flag = False # write to the file or not
			if os.path.isfile(filePath):
				try:
					flag = input("The file \"{0}\" exists. Overwrite the file or not [yN]? ".format(filePath)).upper() in ("Y", "YES", "TRUE", "1")
				except:
					print()
			else:
				flag = True
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
	iRet = EXIT_SUCCESS if results and all([all([r == roundCount for r in result[6:9]] + [r > 0 for r in result[9:length]]) for result in results]) else EXIT_FAILURE
	print("Please press the enter key to exit ({0}). ".format(iRet))
	try:
		input()
	except:
		print()
	return iRet



if "__main__" == __name__:
	exit(main())