import os
from sys import exit
from hashlib import md5
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
	print("See https://blog.csdn.net/weixin_45726033/article/details/144254189 if necessary. ")
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


class ProtocalHIBME:
	def __init__(self:object, group:None|PairingGroup = None) -> None:
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		self.__l = 30
		self.__mpk = None
		self.__msk = None
		self.__flag = [False] * 7 # to control the procedures
	def __product(self:object, vec:tuple|list|set) -> Element:
		if isinstance(vec, (tuple, list, set)) and vec:
			element = vec[0]
			for ele in vec[1:]:
				element *= ele
		else:
			return self.__group
	def Setup(self:object, l:int = 30) -> tuple: # Setup(l) -> (mpk, msk)
		# Check #
		if isinstance(l, int) and l >= 3: # $l$ must be not smaller than $3$ to complete all the tasks
			self.__l = l
		else:
			self.__l = 30
			print("The variable $l$ must be not smaller than $3$ to complete all the tasks. It has been defaulted to $30$. ")
		
		# Protocal #
		g = self.__group.random(G1) # generate $g \in \mathbb{G}_1$ randomly
		alpha, b1, b2 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $\alpha, b_1, b_2 \in \mathbb{Z}_p^*$ randomly
		s, a = tuple(self.__group.random(ZR) for _ in range(self.__l)), tuple(self.__group.random(ZR) for _ in range(self.__l)) # generate $s_1, s_2, \cdots, s_l, a_1, a_2, \cdots, a_l \in \mathbb{Z}_p^*$ randomly
		g2, g3 = self.__group.random(G2), self.__group.random(G2) # generate $g_2, g_3 \in \mathbb{G}_2$ randomly
		h = tuple(self.__group.random(G2) for _ in range(self.__l)) # generate $h_1, h_2, \cdots, h_l \in \mathbb{G}_2$ randomly (Note that the indexes in implementations are 1 smaller than those in theory)
		H1 = lambda x:self.__group.hash(x, G1) # $H_1:\mathbb{Z}_p^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, G2) # $H_2:\mathbb{Z}_p^* \rightarrow \mathbb{G}_2$
		HHat = lambda x:md5(self.__group.serialize(x)).hexdigest().encode()
		g1 = g ** alpha # $g_1 \gets g^\alpha$
		A = pair(g1, g2) # $A \gets e(g_1, g_2)$
		gBar = g ** b1 # $\bar{g} \gets g^{b_1}$
		gTilde = g ** b2 # $\tilde{g} \gets g^{b_2}$
		g3Bar = g3 ** (1 / b1) # $\bar{g}_3 \gets g_3^{\cfrac{1}{b_1}}$
		g3Tilde = g3 ** (1 / b2) # $\tilde{g}_3 \gets g_3^{\cfrac{1}{b_2}}$
		self.__mpk = (g, g1, g2, g3, gBar, gTilde, g3Bar, g3Tilde) + h + (H1, H2, HHat, A) # $\textit{mpk} \gets (g, g_1, g_2, g_3, \bar{g}, \tilde{g}, \bar{g}_3, \tilde{g}_3, h_1, h_2, \cdots, h_l, H_1, H_2, HHat, A)$
		self.__msk = (g2 ** alpha, b1, b2) + s + a # $\textit{msk} \gets (g_2^\alpha, b_1, b_2, s_1, s_2, \cdots, s_l, a_1, a_2, \cdots, a_l)$
		
		# Flag #
		self.__flag[0] = True
		return (self.__mpk, self.__msk)
	def EKGen(self:object, IDk:tuple) -> tuple: # KGen(mpk, msk, ID_k) -> ek_ID_k
		# Check #
		if not self.__flag[0]:
			print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l: # boundary check
			ID_k = IDk
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print("The variable $\\textit{ID}_k$ should be a tuple whose length $k = \\|\\textit{ID}_k\\|$ is an integer within the closed interval $[2, l)$. It has been generated randomly with a length of ${0} - 1 = {1}$. ".format(self.__l, self.__l - 1))
		
		# Unpack #
		H1 = self.__mpk[-4]
		s, a = self.__msk[3:-self.__l], self.__msk[-self.__l:]
		k = len(ID_k)
		
		# Protocol #
		Ak = self.__product(tuple(a[j] for j in range(k))) # $A_k = \product\limits_{j = 1}^k a_j$
		ek1 = tuple(H1(ID_k[i]) ** (s[i] * Ak) for i in range(k)) # $\textit{ek}_{1, i} \gets H_1(I_i)^{s_iA_k}, \forall i \in \{1, 2, \cdots, k\}$
		ek2 = tuple(s[k + i] * Ak for i in range(self.__l - k)) # $\textit{ek}_{2, k + i} \gets s_{k + i}A_k, \forall i \in \{1, 2, \cdots, l - k\}$
		ek3 = tuple(a[i] for i in range(k, self.__l)) # $\textit{ek}_3 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		ek_ID_k = (ek1, ek2, ek3) # $\textit{ek}_\textit{ID}_k \gets (\textit{ek}_1, \textit{ek}_2, \textit{ek}_3)$
		
		# Flag #
		self.__flag[1] = True
		return ek_ID_k
	def DerivedEKGen(self:object, ekIDkMinus1:tuple, IDk:tuple) -> tuple: # DerivedEKGen(ek_ID_kMinus1, ID_k) -> ek_ID_k
		# Check #
		if self.__flag[1]:
			if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l: # boundary check
				ID_k = IDk
				if isinstance(ekIDkMinus1, tuple) and len(ekIDkMinus1) == 3: # check the length of $\textit{ek}_\textit{ID}_k$
					ek_ID_kMinus1 = ekIDkMinus1
				else:
					ek_ID_kMinus1 = self.EKGen(ID_k[:-1])
					print("The variable $\\textit{ek}_\\textit{ID}_{k - 1}$ is invalid, which has been computed again. ")
			else:
				ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
				print("The variable $\\textit{ID}_k$ should be a tuple whose length $k = \\|\\textit{ID}_k\\|$ is an integer within the closed interval $[2, l)$. It has been generated randomly with a length of ${0} - 1 = {1}$. ".format(self.__l, self.__l - 1))
				ek_ID_kMinus1 = self.EKGen(ID_k[:-1])
				print("The variable $\\textit{ek}_\\textit{ID}_k$ is generated correspondingly. ")
		else:
			if self.__flag[0]:
				print("The ``EKGen`` procedure has not been called yet. The program will call the ``EKGen`` with $\\textit{ID}_k$ generated randomly first and finish the ``DerivedEKGen`` subsequently. ")
			else:
				print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup``, ``EKGen``, and ``DerivedEKGen`` in sequence. ")
				self.Setup()
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			ek_ID_kMinus1 = self.EKGen(ID_k[:-1])
		
		# Unpack #
		H1 = self.__mpk[-4]
		a = self.__msk[-self.__l:]
		ek1Minus1, ek2Minus1, ek3Minus1 = ek_ID_kMinus1
		k = len(ID_k)
		
		# Protocal #
		ek1 = tuple(ek1Minus1[i] ** a[k - 1] for i in range(k - 1)) # $\textit{ek}'_{1, i} \gets \textit{ek}_{1, i}^{a_k}, \forall i \in \{1, 2, \cdots, k - 1\}$
		ek2 = tuple(ek2Minus1[i] * a[k - 1] for i in range(1, self.__l - k + 1)) # $\textit{ek}'_{2, i} \gets \textit{ek}_{2, i} \cdot a_k, \forall i \in \{2, 3, \cdots, l - k + 1\}$
		ek1k = H1(ID_k[k - 1]) ** ek2Minus1[0] # $\textit{ek}'_{1, k} \gets H_1(I_k)^{\textit{ek}_{2, 1}$
		ek1 = ek1 + (ek1k, ) # $\textit{ek}'_1 \gets \textit{ek}'_1 || \langle\textit{ek}'_{1, k}\rangle$
		ek3 = tuple(a[i] for i in range(k, self.__l)) # $\textit{ek}'_3 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		ek_ID_k = (ek1, ek2, ek3) # $\textit{ek}_\textit{ID}_k \gets (\textit{ek}'_1, \textit{ek}'_2, \textit{ek}'_3)$
		
		# Flag #
		self.__flag[2] = True
		return ek_ID_k
	def DKGen(self:object, IDk:tuple) -> tuple: # DKGen(msk, ID_k) -> dk_ID_k
		# Check #
		if not self.__flag[0]:
			print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l: # boundary check
			ID_k = IDk
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print("The variable $\\textit{ID}_k$ should be a tuple whose length $k = \\|\\textit{ID}_k\\|$ is an integer within the closed interval $[2, l)$. It has been generated randomly with a length of ${0} - 1 = {1}$. ".format(self.__l, self.__l - 1))
		
		# Unpack #
		g, g1, g2, g3, gBar, gTilde, g3Bar, g3Tilde, h = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[8:-4]
		g2ToThePowerOfAlpha, b1, b2 = self.__msk[0], self.__msk[1], self.__msk[2]
		k = len(ID_k)
		
		# Protocal #
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_p^*$ randomly
		HI = self.__product(tuple(h[i] ** ID_k[i] for i in range(k))) # $\textit{HI} \gets h_1^{I_1} h_2^{I_2} \cdots h_k^{I_k}$
		a0 = g2ToThePowerOfAlpha / g2 ** b1 * HI ** (r / b1) * g3Bar ** r # $g_2^{\cfrac{\alpha}{b_1}} \cdot \textit{HI}^{\cfrac{r}{b_1}} \cdot \bar{g}_3^r$
		a1 = g2ToThePowerOfAlpha / g2 ** b2 * HI ** (r / b2) * g3Tilde ** r # $g_2^{\cfrac{\alpha}{b_2}} \cdot \textit{HI}^{\cfrac{r}{b_2}} \cdot \tilde{g}_3^r$
		Ak = self.__product(tuple(a[j] for j in range(k))) # A_k \gets \product\limits_{j = 1}^k a_j$
		dk2 = tuple(H1(ID_k[i]) ** (s[i] * Ak) for i in range(k)) # $\textit{dk}_{2, i} \gets H_1(I_i)^{s_iA_k}, \forall i \in \{1, 2, \cdots, k\}$
		dk3 = tuple(s[k + i - 1] * A[k - 1] for i in range(self.__l - k)) # $\textit{dk}_{3, i} \gets s_{k + i}A_k, \forall i \in \{1, 2, \cdots, l - k\}$
		dk1 = ( # $\textit{dk}_1 \gets (
			(a0, a1, g ** r) # a_0, a_1, g^r, 
			+ tuple(h[i] ** (r / b1) for i in range(k, self.__l)) # h_{k + 1}^{\cfrac{r}{b_1}}, h_{k + 2}^{\cfrac{r}{b_1}}, \cdots, h_l^{\cfrac{r}{b_1}}, 
			+ tuple(h[i] ** (r / b2) for i in range(k, self.__l)) # h_{k + 1}^{\cfrac{r}{b_2}}, h_{k + 2}^{\cfrac{r}{b_2}}, \cdots, h_l^{\cfrac{r}{b_2}}, 
			+ tuple(h[i] ** (b1 ** (-1)) for i in range(k, self.__l)) # h_{k + 1}^{b_1^{-1}}, h_{k + 2}^{b_1^{-1}}, \cdots, h_l^{b_1^{-1}}, 
			+ tuple(h[i] ** (b2 ** (-1)) for i in range(k, self.__l)) # h_{k + 1}^{b_2^{-1}}, h_{k + 2}^{b_2^{-1}}, \cdots, h_2^{b_1^{-1}}, 
			+ (HI ** (1 / b1), HI ** (1 / b2)) # \textit{HI}^{\cfrac{1}{b_1}}, \textit{HI}^{\cfrac{1}{b_2}}
		) # )$
		dk4 = tuple(a[i] for i in range(k, self.__l)) # $\textit{dk}_4 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		dk_ID_k = (dk1, dk2, dk3, dk4) # $\textit{dk}_\textit{ID}_k \gets (\textit{dk}_1, \textit{dk}_2, \textit{dk}_3, \textit{dk}_4)$
		
		# Flag #
		self.__flag[3] = True
		return dk_ID_k
	def DerivedDKGen(self:object, dkIDkMinus1:tuple, IDk:tuple) -> tuple: # DerivedDKGen(dk_ID_kMinus1, ID_k) -> dk_ID_k
		# Check #
		if self.__flag[1]:
			if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l: # boundary check
				ID_k = IDk
				if isinstance(dkIDkMinus1, tuple) and len(dkIDkMinus1) == 4: # check the length of $\textit{dk}_\textit{ID}_k$
					dk_ID_kMinus1 = dkIDkMinus1
				else:
					dk_ID_kMinus1 = self.DKGen(ID_k[:-1])
					print("The variable $\\textit{dk}_\\textit{ID}_{k - 1}$ is invalid, which has been computed again. ")
			else:
				ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
				print("The variable $\\textit{ID}_k$ should be a tuple whose length $k = \\|\\textit{ID}_k\\|$ is an integer within the closed interval $[2, l)$. It has been generated randomly with a length of ${0} - 1 = {1}$. ".format(self.__l, self.__l - 1))
				dk_ID_kMinus1 = self.DKGen(ID_k[:-1])
				print("The variable $\\textit{dk}_\\textit{ID}_k$ is generated correspondingly. ")
		else:
			if self.__flag[0]:
				print("The ``DKGen`` procedure has not been called yet. The program will call the ``DKGen`` with $\\textit{ID}_k$ generated randomly first and finish the ``DerivedDKGen`` subsequently. ")
			else:
				print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup``, ``DKGen``, and ``DerivedDKGen`` in sequence. ")
				self.Setup()
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			dk_ID_kMinus1 = self.DKGen(ID_k[:-1])
		
		# Unpack #
		H1 = self.__mpk[-4]
		a = self.__msk[-self.__l:]
		k = len(ID_k)
		dk1Minus1, dk2Minus1, dk3Minus1, dk4Minus1 = dk_ID_kMinus1
		a0Minus1, a1Minus1, bMinus1 = dk1Minus1[0], dk1Minus1[1], dk1Minus1[2]
		lengthPerToken = self.__l - k + 1
		c0Minus1, c1Minus1, d0Minus1, d1Minus1 = dk1Minus1[3:3 + lengthPerToken], dk1Minus1[3 + lengthPerToken:3 + (lengthPerToken << 1)], dk1Minus1[-2 - (lengthPerToken << 1):-2 - lengthPerToken], dk1Minus1[-2 - lengthPerToken:-2]
		f0Minus1, f1Minus1 = dk1Minus1[-2], dk1Minus1[-1]
		
		# Protocal #
		t = self.__group.random(ZR) # generate $t \in \mathbb{Z}_p^*$ randomly
		a0 = a0Minus1 * c0Minus1[k - 1] ** ID_k[k - 1] * (f0Minus1 * d0Minus1[k - 1] ** ID_k[k - 1] * g3Bar) ** t # $a'_0 \gets a_0 \cdot c_{0, k}^{I_k} \cdot (f_0 \cdot d_{0, k}^{I_k} \cdot \bar{g}_3)^t$
		a1 = a1Minus1 * c1Minus1[k - 1] ** ID_k[k - 1] * (f1Minus1 * d1Minus1[k - 1] ** ID_k[k - 1] * g3Tilde) ** t # $a'_1 \gets a_1 \cdot c{1, k}^{I_k} \cdot (f_1 \cdot d_{1, k}^{I_k} \cdot \tilde{g}_3)^t$
		dk2 = tuple(dk2Minus1[i] ** a[k - 1] for i in range(k - 1)) # $\textit{dk}'_{2, i} \gets \textit{dk}_{2, i}^{a_k}, \forall i \in \{1, 2, \cdots, k - 1\}$
		dk3 = tuple(dk3Minus1[i] ** a[k - 1] for i in range(1, self.__l - k + 1)) # $\textit{dk}'_{3, i} \gets \textit{dk}_{3, i} \cdot a_k, \forall i \{2, 3, \cdots, l - k + 1\}$
		dk2k = H1(ID_k[k - 1]) ** dk3[0] # $\textit{dk}'_{2, k} \gets H_1(I_k)^{\textit{dk}_{3, 1}}$
		dk2 = dk2 + (dk2k, ) # $\textit{dk}'_2 \gets \textit{dk}'_2 || \langle\textit{dk}'_{2, k}\rangle$
		dk1 = ( # $\textit{dk}'_1 \gets (
			(a0, a1, b * g ** t) # a'_0, a'_1, b \cdot g^t, 
			+ tuple(c0Minus1[i] * d0Minus1[i] ** t for i in range(k, l)) # c_{0, k + 1} \cdot d_{0, k + 1}^t, c_{0, k + 2} \cdot d_{0, k + 2}^t, \cdots, c_{0, l} \cdot d_{0, l}^t, 
			+ tuple(c1Minus1[i] * d1Minus1[i] ** t for i in range(k, l)) # c_{1, k + 1} \cdot d_{1, k + 1}^t, c_{1, k + 2} \cdot d_{1, k + 2}^t, \cdots, c_{1, l} \cdot d_{1, l}^t, 
			+ tuple(d0[i] for i in range(k, l)) # d_{0, k + 1}, d_{0, k + 2}, \cdots, d_{0, l}, 
			+ tuple(d1[i] for i in range(k, l)) # d_{1, k + 1}, d_{1, k + 2}, \cdots, d_{1, l}, 
			(f0 * c0[k - 1] ** ID_k[k - 1], f1 * c1[k - 1] ** ID_k[k - 1]) # f_0 \cdot c_{0, k}^{I_k}, f_1 \cdot c_{1, k}^{I_k}
		) # )$
		dk4 = tuple(a[k + i] for i in range(l - k)) # $\textit{dk}'_4 \gets (a_{k + 1}, a_{k + 2}, \cdots, a_l)$
		dk_ID_k = (dk1, dk2, dk3, dk4) # $\textit{dk}_\textit{ID}_k \gets (\textit{dk}'_1, \textit{dk}'_2, \textit{dk}'_3, \textit{dk}'_4)$
				
		# Flag #
		self.__flag[3] = True
		return dk_ID_k
	def randomElement(self:object, elementField:int = GT) -> Element:
		if not self.__flag[0]:
			print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first before a random element is generated. ")
			self.Setup()
		if elementField in (G1, G2, GT, ZR):
			return self.__group.random(elementField)
		else:
			print("The element field is invalid. It is defaulted to $\\mathbb{G}_T$. ")
			return self.__group.random(GT)
	def Enc(self:object, ekIDS:tuple, IDS:tuple, IDRev:tuple, message:Element) -> Element: # Enc(ek_ID_S, ID_Rev, M) -> CT
		# Check #
		if not self.__flag[0]:
			print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		#####
		if isinstance(ekIDS, tuple) and isinstance(IDS, tuple) and isinstance(IDRev, tuple):
			ek_ID_S, ID_S, ID_Rev = ekIDS, IDS, IDRev
		if isinstance(message, Element):
			M = message
		else:
			M = self.randomElement()
			print("The message passed should be a $\\mathbb{G}_T$ element but it is not. It will be generated randomly. ")
		
		# Unpack #
		n, m = len(ID_S), len(ID_Rev)
		g, g1, g2, g3, gBar, gTilde, g3Bar, g3Tilde, h = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[8:]
		
		# Protocal 
		s1, s2 = self.__group.random(ZR), self.__group.random(ZR) # generate $s_1, s_2 \in \mathbb{Z}_p^*$ randomly
		T = A ** (s1 + s2) # $T \gets A^{s_1 + s_2}$
		eta = self.__group.random(ZR) # generate $\eta \in \mathbb{Z}_p^*$ randomly
		if m == n: # If $m = n$:
			K = self.__product(tuple(pair(g ** eta * ek1[i], H2(ID_Rev[i])) for i in range(n))) # $K \gets \product_{i = 1}^n e(g^{\eta} \cdot \textit{ek}_{1, i}, H_2(I'_i))$
		elif m > n: # If $m > n$:
			An = self.__product(tuple(a[i] for i in range(n))) # $A_n \gets \product\limits_{i = 1}^n a_i$
			Bmn = self.__product(tuple(a[i] for i in range(n, m))) $B_n^m \gets \product\limits_{i = n + 1}^m a_i$
			K = ( # $K \gets
				( # (
					self.__product(tuple(pair(ek1[i], H2(ID_Rev[i])) for i in range(n))) # \product\limits_{i = 1}^n e(\textit{ek}_{1, i}, H_2(I'_i))
					* self.__product(tuple(pair(H1(ID_S[n - 1]), H2(ID_Rev[i])) ** (a[i] * An) for i in range(n, m))) # \cdot \product\limits_{i = n + 1}^m e(H_1(I_n), H_2(I'_i))^{\alpha_i A_n}
				) ** Bmn # )^{B_n^m}
				* pair(g ** eta, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # \cdot e(g^{\eta}, \product\limits_{i = 1}^m H_2(I'_i))
			) # $
		else: # If $m < n$
			K = ( # $K \gets
				self.__product(tuple(pair(ek1[i], H2(ID_Rev[i])) for i in range(m))) # \product\limits_{i = 1}^m e(\textit{ek}_{1, i}, H_2(I'_i))
				* self.__product(tuple(pair(ek1[i], H2(ID_Rev[m - 1])) for i in range(m, n))) # \product\limits_{i = m + 1}^n e(\textit{ek}_{1, i}, H_2(I'_m))
				* pair(g ** eta, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # e(g^{\eta}, \product\limits_{i = 1}^m H_2(I'_i))
			) # $
		C1 = self.__xor(self.__xor(M, HHat(T)), HHat(K)) # $C_1 \gets M \oplus \hat{H}(T) \oplus \hat{H}(K)$
		C2 = gBar ** s1 # $C_2 \gets \bar{g}^{s_1}$
		C3 = gTilde ** s2 # $C_3 \gets \tilde{g}^{s_2}$
		C4 = (self.__product(tuple(h[i] ** ID_S[i] for i in range(k))) * g3) ** (s1 + s2) # $C_4 \gets (h_1^{I_1} h_2^{I_2} \cdots h_k^{I_k} \cdot g_3)^{s_1 + s_2}$
		C5 = g ** eta # $C_5 \gets g^{\eta}$
		CT = (C1, C2, C3, C4, C5) # $\textit{CT} \gets (C_1, C_2, C_3, C_4, C_5)$
		
		# Flag #
		self.__flag[5] = True
		return CT
	def Dec(self:object, cipher:tuple, ekIDk:tuple) -> bytes: # Dec(CT, ek_ID_k) -> M
		# Check #
		if self.__flag[1]:
			if isinstance(ekIDk, tuple) and len(ekIDk) >= 9 and isinstance(cipher, tuple) and 5 == len(cipher):
				CT, ek_ID_k = cipher, ekIDk
			else:
				print(
					"At least one of the variables $\\textit{CT}$ and $\\textit{ek}_\\textit{ID}_k$ is invalid. "
					+ "The program will call the ``EKGen`` with $\\textit{ID}_k$ generated randomly, the ``Enc`` with $M \in \\{0, 1\\}^\\lambda$ generated randomly, and the ``Dec`` in sequence. "
				)
				ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
				CT = self.Enc(ID_k, b"ProtocalHIBME")
				ek_ID_k = self.EKGen(ID_k)
		else:
			if self.__flag[0]:
				print("The ``KGen`` procedure has not been called yet. The program will call the ``KGen`` with $\\textit{ID}_k$ generated randomly first and finish the ``Dec`` subsequently. ")
			else:
				print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup``, ``KGen``, and ``Dec`` in sequence. ")
				self.Setup()
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			ek_ID_k = self.EKGen(ID_k)
		
		# Unpack #
		C1, C2, C3, C4, C5 = CT
		
		# Protocal #
		TPi = pair(dk1[2], C4) / (pair(C2, dk1[0]) * pair(C3, dk1[1])) # $T' = \cfrac{e(\textit{dk}_{1, 3}, C_4)}{e(C_2, \textit{dk}_{1, 1})e(C_3, \textit{dk}_{1, 2})}$
		if m == n: # If $m = n$:
			KPi = ( # $K' \gets
				self.__product(tuple(pair(H1(ID_Snd[i]), dk2[i]) for i in rannge(n))) # \product\limits_{i = 1}^n e(H_1(I_i), \textit{dk}_{2, i})
				 * pair(C5, self.__product(tuple(H2(ID_R[i]) for i in range(n)))) # \cdot e(C_5, \product\limits_{i = 1}^n H_2(I'_i))
			) # $
		elif m > n: # If $m > n$:
			KPi = ( # $K' \gets
				self.__product(tuple(pair(H1(ID_Snd[i]), dk2[i]) for i in range(n))) # \product\limits_{i = 1}^n e(H_1(I_i), \textit{dk}_{2, i})
				* self.__product(tuple(pair(H1(ID_Snd[m - 1], dk2[i]) for i in range(n, m))) # \cdot \product\limits_{i = n+ 1}^m e(H_1(I_m), \textit{dk}_{2, i})
				* pair(C5, self.__product(tuple(H2(ID_Rev[i]) for i in range(m))) # \cdot \product\limits_{i = 1}^m H_2(I'_i))
			) # $
		else: # If $m < n$
			Am = self.__product(tuple(a[i] for i in range(m))) # $A_m \gets \product\limits_{i = 1}^m a_i$
			Bnm = self.__product(tuple(a[i] for i in range(m, n))) $B_n^m \gets \product\limits_{i = m + 1}^n a_i$
			KPi = ( # $K' \gets
				( # (
					self.__product(tuple(pair(H1(ID_Snd[i]), dk2[i]) for i in range(n))) # \product\limits_{i = 1}^n e(H_1(I_i), \textit{dk}_{2, i})
					* self.__product(tuple(pair(H1(ID_Snd[i]), H2(ID_Rev[m - 1])) ** (a[i] * Am) for i in range(m, n))) # \cdot \product\limits_{i = m + 1}^n e(H_1(I_i), H_2(I'_m))^{\alpha_i A_m}
				) ** Bnm # )^{B_m^n}
				* pair(C5, self.__product(tuple(H2(ID_Rev[i]) for i in range(m)))) # \cdot e(C_5, \product\limits_{i = 1}^m H_2(I'_i))
			) # $
		M = self.__xor(self.__xor(C1, HHat(TPi)), HHat(KPi)) # $M \gets C_1 \oplus \hat{H}(T') \oplus \hat{H}(K')$
		
		# Flag #
		self.__flag[6] = True
		return M


def protocal(curveType:str, k:int, l:int) -> list:
	# Begin #
	if isinstance(k, int) and isinstance(l, int) and 2 <= k < l:
		try:
			group = PairingGroup(curveType)
		except:
			return [curveType, l, k, False, False] + [-1] * 10
	else:
		return [curveType, l, k, False, False] + [-1] * 10
	process = Process(os.getpid())
	print("Type =", curveType)
	print("l =", l)
	print("k =", k)
	
	# Initialization #
	protocalHIBME = ProtocalHIBME(group)
	timeRecords, memoryRecords = [], []
	
	# Setup #
	startTime = time()
	protocalHIBME.Setup(l)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# EKGen #
	ID_k = tuple(group.random(ZR) for i in range(k))
	startTime = time()
	ek_ID_k = protocalHIBME.EKGen(ID_k)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# DerivedEKGen #
	ek_ID_kMinus1 = protocalHIBME.EKGen(ID_k[:-1]) # remove the last one to generate the ek_ID_kMinus1
	startTime = time()
	ek_ID_kDerived = protocalHIBME.DerivedEKGen(ek_ID_kMinus1, ID_k)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# DKGen #
	startTime = time()
	dk_ID_k = protocalHIBME.DKGen(ID_k)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# DerivedDKGen #
	dk_ID_kMinus1 = protocalHIBME.DKGen(ID_k[:-1]) # remove the last one to generate the dk_ID_kMinus1
	startTime = time()
	dk_ID_kDerived = protocalHIBME.DerivedDKGen(dk_ID_kMinus1, ID_k)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Enc #
	message = protocalHIBME.randomElement(GT)
	startTime = time()
	CT = protocalHIBME.Enc(ID_k, message)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Dec #
	startTime = time()
	M = protocalHIBME.Dec(CT, ek_ID_k)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# End #
	print("message =", message)
	print("M =", M)
	print("Is message == M? {0}".format("Yes" if message == M else "No"))
	print("Time:", timeRecords)
	print("Memory:", memoryRecords)
	print()
	return [curveType, l, k, True, message == M] + timeRecords + memoryRecords

def main() -> int:
	results, fileName = [], "results.xlsx"
	for curveType in ("MNT159", "MNT201", "MNT224"):
		for l in (5, 10, 15, 20, 25, 30):
			for k in range(5, l, 5):
				results.append(protocal(curveType, k, l))
	if results:
		columns = ["Curve", "l", "k", "isValid", "isPassed", "Setup (s)", "KGen (s)", "DerivedKGen (s)", "Enc (s)", "Dec (s)", "Setup (byte)", "KGen (byte)", "DerivedKGen (byte)", "Enc (byte)", "Dec (byte)"]
		try:
			df = __import__("pandas").DataFrame(results, columns = columns)
			if os.path.splitext(fileName)[0].lower() == ".csv":
				df.to_csv(fileName, index = False)
			else:
				df.to_excel(fileName, index = False)
			print("\nSuccessfully saved the results to \"{0}\" in the three-line table form. ".format(fileName))
		except:
			try:
				with open(fileName, "w", encoding = "utf-8") as f:
					f.write(str(columns) + "\n" + str(results))
				print("\nSuccessfully saved the results to \"{0}\" in the plain text form. ".format(fileName))
			except BaseException as e:
				print("\nResults: \n{0}\n\nFailed to save the results to \"{1}\" since {2}. \nPlease press the enter key to exit. ".format(results, fileName, e))
				input()
				return EOF
	else:
		print("The results are empty. Please press the enter key to exit. ")
		input()
		return EOF
	print("Please press the enter key to exit. ")
	input()
	return EXIT_SUCCESS if all([result[1] for result in results]) else EXIT_FAILURE



if "__main__" == __name__:
	exit(main())