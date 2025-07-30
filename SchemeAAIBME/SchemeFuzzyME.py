import os
from sys import argv, exit
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
from random import shuffle
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


class SchemeFuzzyME:
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
		self.__n = 30
		self.__d = 10
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
	def Setup(self:object, n:int = 30, d:int = 10) -> tuple: # $\textbf{Setup}(n, d) \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		if isinstance(n, int) and n >= 1: # boundary check
			self.__n = n
		else:
			self.__n = 30
			print("Setup: The variable $n$ should be a positive integer but it is not, which has been defaulted to $30$. ")
		if isinstance(d, int) and d >= 2: # boundary check
			self.__d = d
		else:
			self.__d = 10
			print("Setup: The variable $d$ should be a positive integer not smaller than $2$ but it is not, which has been defaulted to $10$. ")
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		g2, g3 = self.__group.random(G1), self.__group.random(G1) # generate $g_2, g_3 \in \mathbb{G}_1$ randomly
		tVec = tuple(self.__group.random(G1) for _ in range(n + 1)) # generate $\vec{t} = (t_1, t_2, \cdots, t_{n + 1}) \in \mathbb{G}_1^{n + 1}$ randomly
		lVec = tuple(self.__group.random(G1) for _ in range(n + 1)) # generate $\vec{l} = (l_1, l_2, \cdots, l_{n + 1}) \in \mathbb{G}_1^{n + 1}$ randomly
		alpha, beta, theta1, theta2, theta3, theta4 = self.__group.random(ZR, 6) # generate $\alpha, \beta, \theta_1, \theta_2, \theta_3, \theta_4 \in \mathbb{Z}_r$ randomly
		g1 = g ** alpha # $g_1 \gets g^\alpha$
		eta1 = g ** theta1 # $\eta_1 \gets g^{\theta_1}$
		eta2 = g ** theta2 # $\eta_2 \gets g^{\theta_2}$
		eta3 = g ** theta3 # $\eta_3 \gets g^{\theta_3}$
		eta4 = g ** theta4 # $\eta_4 \gets g^{\theta_4}$
		Y1 = pair(g1, g2) ** (theta1 * theta2) # $Y_1 \gets \hat{e}(g_1, g_2)^{\theta_1 \theta_2}$
		Y2 = pair(g3, g ** beta) ** (theta1 * theta2) # $Y_2 \gets \hat{e}(g_3, g^\beta)^{\theta_1 \theta_2}$
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		self.__mpk = (g1, g2, g3, Y1, Y2, tVec, lVec, eta1, eta2, eta3, eta4, H1) # $ \textit{mpk} \gets (g_1, g_2, g_3, Y_1, Y_2, \vec{t}, \vec{l}, \eta_1, \eta_2, \eta_3, \eta_4, H_1)$
		self.__msk = (alpha, beta, theta1, theta2, theta3, theta4) # $\textit{msk} \gets (\alpha, \beta, \theta_1, \theta_2, \theta_3, \theta_4)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, SA:tuple) -> tuple: # $\textbf{EKGen}(S_A) \rightarrow \textit{ek}_{S_A}$
		# Check #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(SA, tuple) and len(SA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in SA): # hybrid check
			S_A = SA
		else:
			S_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("EKGen: The variable $S_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g3, lVec = self.__mpk[2], self.__mpk[6]
		beta, theta1, theta2 = self.__msk[1], self.__msk[2], self.__msk[3]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta: i, S, x \rightarrow \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		N = tuple(range(1, self.__n + 2)) # $N \gets (1, 2, \cdots, n + 1)$
		H = lambda x:g3 ** (x ** self.__n) * self.__product(tuple(lVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $H: x \rightarrow g_3^{x^n} \prod\limits_{i = 1}^{n + 1} l_i^{\Delta(i, N, x)}$
		coefficients = (beta, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		q = lambda x:self.__computePolynomial(x, coefficients) # generate a $(d - 1)$ degree polynominal $q(x)$ s.t. $q(0) = \beta$ randomly
		rVec = tuple(self.__group.random(ZR) for _ in S_A) # generate $\vec{r} = (r_1, r_2, \cdots, r_n) \in \mathbb{Z}_r^n$ randomly
		EVec = tuple(g3 ** (q(S_A[i]) * theta1 * theta2) * H(S_A[i]) ** rVec[i] for i in range(len(S_A))) # $E_i \gets g_3^{q(a_i) \theta_1 \theta_2} H(a_i)^{r_i}, \forall i \in \{1, 2, \cdots, n\}$
		eVec = tuple(g ** rVec[i] for i in range(len(S_A))) # $e_i \gets g^{r_i}, \forall i \in \{1, 2, \cdots, n\}$
		ek_S_A = (EVec, eVec) # $\textit{ek}_{S_A} \gets \{E_i, e_i\}_{a_i \in S_A}$
		
		# Return #
		return ek_S_A # \textbf{return} $\textit{ek}_{S_A}$
	def DKGen(self:object, SB:tuple, PA:tuple) -> tuple: # $\textbf{DKGen}(\textit{id}_R) \rightarrow \textit{dk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(SB, tuple) and len(SB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in SB): # hybrid check
			S_B = SB
		else:
			S_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("DKGen: The variable $S_B$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(PA, tuple) and len(PA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in PA): # hybrid check
			P_A = PA
		else:
			P_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("DKGen: The variable $P_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g2, g3, tVec, lVec = self.__mpk[1], self.__mpk[2], self.__mpk[5], self.__mpk[6]
		alpha, beta, theta1, theta2, theta3, theta4 = self.__msk[0], self.__msk[1], self.__msk[2], self.__msk[3], self.__msk[4], self.__msk[5]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta: i, S, x \rightarrow \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		N = tuple(range(1, self.__n + 2)) # $N \gets (1, 2, \cdots, n + 1)$
		T = lambda x:g2 ** (x ** self.__n) * self.__product(tuple(tVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $T: x \rightarrow g_2^{x^n} \prod\limits_{i = 1}^{n + 1} t_i^{\Delta(i, N, x)}$
		H = lambda x:g3 ** (x ** self.__n) * self.__product(tuple(lVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $H: x \rightarrow g_3^{x^n} \prod\limits_{i = 1}^{n + 1} l_i^{\Delta(i, N, x)}$
		gamma = self.__group.random(ZR) # generate $\gamma \in \mathbb{Z}_r$ randomly
		G_ID = self.__group.random(G1) # generate $G_{\textit{ID}} \in \mathbb{G}_1$ randomly
		coefficientsForF = (alpha, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		f = lambda x:self.__computePolynomial(x, coefficientsForF) # generate a $(d - 1)$ degree polynominal $f(x)$ s.t. $f(0) = \alpha$ randomly
		coefficientsForH = (gamma, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		h = lambda x:self.__computePolynomial(x, coefficientsForH) # generate a $(d - 1)$ degree polynominal $h(x)$ s.t. $h(0) = \gamma$ randomly
		coefficientsForQPrime = (beta, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		qPrime = lambda x:self.__computePolynomial(x, coefficientsForQPrime) # generate a $(d - 1)$ degree polynominal $q'(x)$ s.t. $q'(0) = \beta$ randomly
		k1Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{k}_1 = (k_{1, 1}, k_{1, 2}, \cdots, k_{1, n}) \in \mathbb{Z}_r^n$ randomly
		k2Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{k}_2 = (k_{2, 1}, k_{2, 2}, \cdots, k_{2, n}) \in \mathbb{Z}_r^n$ randomly
		rPrime1Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{r}'_1 = (r'_{1, 1}, r'_{1, 2}, \cdots, r'_{1, n}) \in \mathbb{Z}_r^n$ randomly
		rPrime2Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{r}'_2 = (r'_{2, 1}, r'_{2, 2}, \cdots, r'_{2, n}) \in \mathbb{Z}_r^n$ randomly
		dk_S_B_0 = tuple(g ** (k1Vec[i] * theta1 * theta2 + k2Vec[i] * theta3 * theta4) for i in range(self.__n)) # $\textit{dk}_{S_{B_{0, i}}} \gets g^{k_{1, i} \theta_1 \theta_2 + k_{2, i} \theta_3 \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_1 = tuple(																						\
			g2 ** (-f(S_B[i]) * theta2) * G_ID ** (-h(S_B[i]) * theta2) * T(S_B[i]) ** (-k1Vec[i] * theta2) for i in range(self.__n)	\
		) # $\textit{dk}_{S_{B_{1, i}}} \gets g_2^{-f(b_i) \theta_2} (G_{\textit{ID}})^{-h(b_i) \theta_2} [T(b_i)]^{-k_{1, i} \theta_2}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_2 = tuple(																						\
			g2 ** (-f(S_B[i]) * theta1) * G_ID ** (-h(S_B[i]) * theta1) * T(S_B[i]) ** (-k1Vec[i] * theta1) for i in range(self.__n)	\
		) # $\textit{dk}_{S_{B_{2, i}}} \gets g_2^{-f(b_i) \theta_1} (G_{\textit{ID}})^{-h(b_i) \theta_1} [T(b_i)]^{-k_{1, i} \theta_1}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_3 = tuple(T(S_B[i]) ** (-k2Vec[i] * theta4) for i in range(self.__n)) # $\textit{dk}_{S_{B_{3, i}}} \gets [T(b_i)]^{-k_{2, i} \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B_4 = tuple(T(S_B[i]) ** (-k2Vec[i] * theta3) for i in range(self.__n)) # $\textit{dk}_{S_{B_{4, i}}} \gets [T(b_i)]^{-k_{2, i} \theta_3}, \forall i \in \{1, 2, \cdots, n\}$
		dk_S_B = (dk_S_B_0, dk_S_B_1, dk_S_B_2, dk_S_B_3, dk_S_B_4) # $\textit{dk}_{S_B} \gets (\textit{dk}_{S_{B_0}}, \textit{dk}_{S_{B_1}}, \textit{dk}_{S_{B_2}}, \textit{dk}_{S_{B_3}}, \textit{dk}_{S_{B_4}})$
		dk_P_A_0 = tuple(g ** (rPrime1Vec[i] * theta1 * theta2 + rPrime2Vec[i] * theta3 * theta4) for i in range(self.__n)) # $\textit{dk}_{P_{A_{0, i}}} \gets g^{r'_{i, 1} \theta_1 \theta_2 + r'_{i, 2} \theta_3 \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_1 = tuple(																										\
			g2 ** (-2 * qPrime(P_A[i]) * theta2) * G_ID ** (h(P_A[i]) * theta2) * H(P_A[i]) ** (-rPrime1Vec[i] * theta2) for i in range(self.__n)		\
		) # $\textit{dk}_{P_{A_{1, i}}} \gets g_2^{-2q'(a_i) \theta_2} (G_{\textit{ID}})^{h(a_i \theta_2)} H(a_i)^{-r'_{1, i} \theta_2}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_2 = tuple(																										\
			g2 ** (-2 * qPrime(P_A[i]) * theta1) * G_ID ** (h(P_A[i]) * theta1) * H(P_A[i]) ** (-rPrime1Vec[i] * theta1) for i in range(self.__n)		\
		) # $\textit{dk}_{P_{A_{2, i}}} \gets g_2^{-2q'(a_i) \theta_1} (G_{\textit{ID}})^{h(a_i \theta_1)} H(a_i)^{-r'_{1, i} \theta_1}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_3 = tuple(H(P_A[i]) ** (-rPrime2Vec[i] * theta4) for i in range(self.__n)) # $\textit{dk}_{P_{A_{3, i}}} \gets [H(a_i)]^{-r'_{2, i} \theta_4}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A_4 = tuple(H(P_A[i]) ** (-rPrime2Vec[i] * theta3) for i in range(self.__n)) # $\textit{dk}_{P_{A_{3, i}}} \gets [H(a_i)]^{-r'_{2, i} \theta_3}, \forall i \in \{1, 2, \cdots, n\}$
		dk_P_A = (dk_P_A_0, dk_P_A_1, dk_P_A_2, dk_P_A_3, dk_P_A_4) # $\textit{dk}_{P_A} \gets (\textit{dk}_{P_{A_0}}, \textit{dk}_{P_{A_1}}, \textit{dk}_{P_{A_2}}, \textit{dk}_{P_{A_3}}, \textit{dk}_{P_{A_4}})$
		dk_SBPA = (dk_S_B, dk_P_A) # $\textit{dk}_{S_B, P_A} \gets (\textit{dk}_{S_B}, \textit{dk}_{P_A})$
		
		# Return #
		return dk_SBPA # \textbf{return} $\textit{dk}_{S_B, P_A}$
	def Encryption(self:object, ekSA:tuple, SA:tuple, PB:tuple, message:Element) -> tuple: # $\textbf{Encryption}(\textit{ek}_{S_A}, M) \rightarrow \textit{CT}$
		# Check #
		if not self.__flag:
			print("Encryption: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Encryption`` subsequently. ")
			self.Setup()
		if isinstance(SA, tuple) and len(SA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in SA): # hybrid check
			S_A = SA
			if isinstance(ekSA, tuple) and len(ekSA) == 2 and isinstance(ekSA[0], tuple) and isinstance(ekSA[1], tuple) and len(ekSA[0]) == len(ekSA[1]) == self.__n: # hybrid check
				ek_S_A = ekSA
			else:
				ek_S_A = self.EKGen(S_A)
				print("Encryption: The variable $\\textit{ek}_{S_A}$ should be a tuple containing 2 tuples but it is not, which has been generated accordingly. ")
		else:
			S_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Encryption: The variable $S_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			ek_S_A = self.EKGen(S_A)
			print("Encryption: The variable $\\textit{ek}_{S_A}$ has been generated accordingly. ")
		if isinstance(PB, tuple) and len(PB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in PB): # hybrid check
			P_B = PB
		else:
			P_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Encryption: The variable $P_B$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			M = message
		else:
			M = self.__group.random(GT)
			print("Encryption: The variable $M$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g2, g3, Y1, Y2, tVec, lVec, eta1, eta2, eta3, eta4, H1 = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[9], self.__mpk[10], self.__mpk[11]
		EVec, eVec = ek_S_A
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # $\Delta: i, S, x \rightarrow \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
		N = tuple(range(1, self.__n + 2)) # $N \gets (1, 2, \cdots, n + 1)$
		T = lambda x:g2 ** (x ** self.__n) * self.__product(tuple(tVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $T: x \rightarrow g_2^{x^n} \prod\limits_{i = 1}^{n + 1} t_i^{\Delta(i, N, x)}$
		H = lambda x:g3 ** (x ** self.__n) * self.__product(tuple(lVec[i] ** Delta(i, N, x) for i in range(self.__n + 1))) # $H: x \rightarrow g_3^{x^n} \prod\limits_{i = 1}^{n + 1} l_i^{\Delta(i, N, x)}$
		s, s1, s2, tau = self.__group.random(ZR, 4) # generate $s, s_1, s_2, \tau \in \mathbb{Z}_r$ randomly
		K_s = Y1 ** s # $K_s \gets Y_1^s$
		K_l = Y2 ** s * pair(g3, g ** (-tau)) # $K_l \gets Y_2^s \cdot \hat{e}(g_3, g^{-\tau})$
		C0 = M * K_s * K_l # $C_0 \gets M \cdot K_s \cdot K_l$
		C1 = eta1 ** (s - s1) # $C_1 \gets \eta_1^{s - s_1}$
		C2 = eta2 ** s1 # $C_2 \gets \eta_2^{s_1}$
		C3 = eta3 ** (s - s2) # $C_3 \gets \eta_3^{s - s_2}$
		C4 = eta4 ** s2 # $C_4 \gets \eta_4^{s_2}$
		C1Vec = tuple(T(P_B[i]) ** s for i in range(len(P_B))) # $C_{1, i} \gets T(b_i)^s, \forall b_i \in P_B$
		C2Vec = tuple(H(S_A[i]) ** s for i in range(len(S_A))) # $C_{2, i} \gets H(a_i)^s, \forall a_i \in S_A$
		coefficients = (tau, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		l = lambda x:self.__computePolynomial(x, coefficients) # generate a $(d - 1)$ degree polynominal $l(x)$ s.t. $l(0) = \tau$ randomly
		xiVec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{\xi} = (\xi_1, \xi_2, \cdots, \xi_n) \in \mathbb{Z}_r^n$ randomly
		chiVec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{\chi} = (\chi_1, \chi_2, \cdots, \chi_n) \in \mathbb{Z}_r^n$ randomly
		C3Vec = tuple(eVec[i] * g ** xiVec[i] for i in range(self.__n)) # $C_{3, i} \gets e_i \cdot g^{\xi_i}, \forall i \in \{1, 2, \cdots, n\}$
		C4Vec = tuple(g ** chiVec[i] for i in range(self.__n)) # $C_{4, i} \gets g^{\chi_i}, \forall i \in \{1, 2, \cdots, n\}$
		C5Vec = tuple(EVec[i] ** s * g3 ** l(S_A[i]) * H(S_A[i]) ** (s * xiVec[i]) * H1(														\
			self.__group.serialize(C0) + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + self.__group.serialize(C4)		\
			+ self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) + self.__group.serialize(C4Vec[i])		\
		) for i in range(self.__n)) # $C_{5, i} \gets E_i^s \cdot g_3^{l(a_i)} H(a_i)^{s \cdot \xi_i} \cdot H_1(C_0 || C_1 || C_2 || C_3 || C_4 || C_{1, i} || C_{2, i} || C_{3, i} || C_{4, i})^{\chi_i}$
		CT = (C0, C1, C2, C3, C4, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec) # $\textit{CT} \gets (C_0, C_1, C_2, C_3, C_4, \vec{C}_1, \vec{C}_2, \vec{C}_3, \vec{C}_4, \vec{C}_5)$
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Decryption(self:object, dkSBPA:tuple, SA:tuple, PA:tuple, SB:tuple, PB:tuple, cipherText:tuple) -> Element|bool: # $\textbf{Decryption}(\textit{dk}_{S_B, P_A}, S_B, P_A, \textit{CT}) \rightarrow M$
		# Check #
		if not self.__flag:
			print("Decryption: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Decryption`` subsequently. ")
			self.Setup()
		if (																																	\
			isinstance(SA, tuple) and isinstance(PA, tuple) and isinstance(SB, tuple) and isinstance(PB, tuple) and len(SA) == len(PA) == len(SA) == len(SB) == self.__n	\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in SA) and all(isinstance(ele, Element) and ele.type == ZR for ele in PA)						\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in SB) and all(isinstance(ele, Element) and ele.type == ZR for ele in PB)						\
		): # hybrid check
			S_A, P_A, S_B, P_B = SA, PA, SB, PB
			if (																																		\
				isinstance(dkSBPA, tuple) and len(dkSBPA) == 2 and isinstance(dkSBPA[0], tuple) and isinstance(dkSBPA[1], tuple) and len(dkSBPA[0]) == len(dkSBPA[1]) == 5	\
				and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in dkSBPA[0]) and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in dkSBPA[1])				\
			): # hybrid check
				dk_SBPA = dkSBPA
			else:
				dk_SBPA = self.DKGen(S_B, P_A)
				print("Decryption: The variable $\\textit{dk}_{S_B, P_A}$ should be a tuple containing 2 tuples but it is not, which has been generated accordingly. ")
		else:
			S_A, P_A = tuple(self.__group.random(ZR) for _ in range(self.__n)), tuple(self.__group.random(ZR) for _ in range(self.__n))
			S_B, P_B = tuple(self.__group.random(ZR) for _ in range(self.__n)), tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Decryption: Each of the variables $S_A$, $P_A$, $S_B$, and $P_B$ should be a tuple containing 4 elements of $\\mathbb{Z}_r$ but at least one of them is not, all of which have been generated randomly. ")
			dk_SBPA = self.DKGen(S_B, P_A)
			print("Decryption: The variable $\\textit{dk}_{S_B, P_A}$ has been generated accordingly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 10 and all(isinstance(ele, Element) for ele in cipherText[:5]) and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in cipherText[5:]): # hybrid check
			CT = cipherText
		else:
			CT = self.Enc(self.EKGen(S_A), S_A, P_B, self.__group.random(GT))
			print("Decryption: The variable $\\textit{CT}$ should be a tuple containing 5 elements and 5 tuples but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[11]
		dk_S_B, dk_P_A = dk_SBPA
		dk_S_B_0, dk_S_B_1, dk_S_B_2, dk_S_B_3, dk_S_B_4 = dk_S_B
		dk_P_A_0, dk_P_A_1, dk_P_A_2, dk_P_A_3, dk_P_A_4 = dk_P_A
		C0, C1, C2, C3, C4, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec = CT
		
		# Scheme #
		WAPrime = set(S_A).intersection(P_A) # $W'_A \gets S_A \cap P_A$
		WBPrime = set(S_B).intersection(P_B) # $W'_B \gets S_B \cap P_B$
		if len(WAPrime) >= self.__d and len(WBPrime) >= self.__d: # \textbf{if} $|W'_A| \leqslant d \land |W'_B| \leqslant d$ \textbf{then}
			WA = tuple(WAPrime)[:self.__d] # \quad generate $W_A \subset W'_A$ s.t. $|W_A| = d$ randomly
			WB = tuple(WBPrime)[:self.__d] # \quad generate $W_B \subset W'_B$ s.t. $|W_B| = d$ randomly
			g = self.__group.init(G1, 1) # \quad$g \gets 1_{\mathbb{G}_1}$
			Delta = lambda i, S, x:self.__product(tuple((x - j) / (i - j) for j in S if j != i)) # \quad$\Delta: i, S, x \rightarrow \prod\limits_{j \in S, j \neq i} \frac{x - j}{i - j}$
			KsPrime = self.__product(
				tuple((pair(C1Vec[i], dk_S_B_0[i]) * pair(C1, dk_S_B_1[i]) * pair(C2, dk_S_B_2[i]) * pair(C3, dk_S_B_3[i]) * pair(C4, dk_S_B_4[i])) ** Delta(S_B[i], WB, 0) for i in range(self.__n))
			) # \quad$K'_s \gets \prod\limits_{b_i \in W_B} (\hat{e}(C_{1, i}, \textit{dk}_{S_{B_{0, i}}}) \hat{e}(C_1, \textit{dk}_{S_{B_{1, i}}}) \hat{e}(C_2, \textit{dk}_{S_{B_{2, i}}}) \hat{e}(C_3, \textit{dk}_{S_{B_{3, i}}}) \hat{e}(C_4, \textit{dk}_{S_{B_{4, i}}}))^{\Delta(b_i, W_B, 0)}$
			CTVec = tuple(																												\
				(																														\
					self.__group.serialize(C0) + self.__group.serialize(C1) + self.__group.serialize(C2) + self.__group.serialize(C3) + self.__group.serialize(C4)		\
					+ self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) + self.__group.serialize(C4Vec[i])		\
				) for i in range(self.__n)																										\
			) # \quad$\textit{CT}_i \gets C_0 || C_1 || C_2 || C_3 || C_4 || C_{1, i} || C_{2, i} || C_{3, i} || C_{4, i}, \forall i \in \{1, 2, \cdots, n\}$
			KlPrime = self.__product(																																									\
				tuple(																																												\
					(																																												\
						(pair(C1Vec[i], dk_P_A_0[i]) * pair(C1, dk_P_A_1[i]) * pair(C2, dk_P_A_2[i])) / (pair(H1(CTVec[i]), C4Vec[i]) * pair(C3Vec[i], C2Vec[i])) * pair(C3, dk_P_A_3[i]) * pair(C4, dk_P_A_4[i]) * pair(C5Vec[i], g)	\
					) ** Delta(S_A[i], WA, 0) for i in range(self.__n)																																			\
				)																																													\
			) # \quad$K'_l \gets \prod\limits_{a_i \in W_A} \left(\frac{\hat{e}(C_{1, i}, \textit{dk}_{P_{A_{0, i}}}) \hat{e}(C_1, \textit{dk}_{P_{A_{1, i}}}) \hat{e}(C_2, \textit{dk}_{P_{A_{i, 2}}})}{\hat{e}(H_1(\textit{CT}_i), C_{4, i}) \cdot \hat{e}(C_{3, i}, C_{2, i})} \cdot \hat{e}(C_3, \textit{dk}_{P_{A_{i, 3}}}) \hat{e}(C_4, \textit{dk}_{P_{A_{i, 4}}}) \hat{e}(C_{5, i}, g)\right)^{\Delta(a_i, W_A, 0)}$
			M = C0 * KsPrime * KlPrime # \quad$M \gets C_0 \cdot K'_s \cdot K'_l$
		else: # \textbf{else}
			M = False # \quad$M \gets \perp$
		# \textbf{end if}
		
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


def Scheme(curveType:tuple|list|str, n:int = 30, d:int = 10, round:int|None = None) -> list:
	# Begin #
	if isinstance(n, int) and isinstance(d, int) and n >= 1 and d >= 2: # no need to check the parameters for curve types here
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
			print("n =", n)
			print("d =", d)
			if isinstance(round, int) and round >= 0:
				print("round =", round)
			print("Is the system valid? No. \n\t{0}".format(e))
			return (																																													\
				([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])	\
				+ [n if isinstance(n, int) else None, d if isinstance(d, int) else None, round if isinstance(round, int) else None] + [False] * 2 + [-1] * 13																			\
			)
	else:
		print("Is the system valid? No. The parameter $n$ should be a positive integer, and the parameter $d$ should be a positive integer not smaller than $2$. ")
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [n if isinstance(n, int) else None, d if isinstance(d, int) else None, round if isinstance(round, int) and round >= 0 else None] + [False] * 2 + [-1] * 13																	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	print("n =", n)
	print("d =", d)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeFuzzyME = SchemeFuzzyME(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeFuzzyME.Setup(n = n, d = d)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# EKGen #
	startTime = perf_counter()
	S_A = tuple(group.random(ZR) for _ in range(n))
	ek_S_A = schemeFuzzyME.EKGen(S_A)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DKGen #
	startTime = perf_counter()
	S_B = tuple(group.random(ZR) for _ in range(n))
	P_A = list(S_A)
	shuffle(P_A)
	P_A = P_A[:d] + list(group.random(ZR) for _ in range(n - d))
	shuffle(P_A)
	P_A = tuple(P_A)
	dk_SBPA = schemeFuzzyME.DKGen(S_B, P_A)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Encryption #
	startTime = perf_counter()
	P_B = list(S_B)
	shuffle(P_B)
	P_B = P_B[:d] + list(group.random(ZR) for _ in range(n - d))
	shuffle(P_B)
	P_B = tuple(P_B)
	message = group.random(GT)
	CT = schemeFuzzyME.Encryption(ek_S_A, S_A, P_B, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Decryption #
	startTime = perf_counter()
	M = schemeFuzzyME.Decryption(dk_SBPA, S_A, P_A, S_B, P_B, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(M, bool) and message == M]
	spaceRecords = [																														\
		schemeFuzzyME.getLengthOf(group.random(ZR)), schemeFuzzyME.getLengthOf(group.random(G1)), schemeFuzzyME.getLengthOf(group.random(GT)), 	\
		schemeFuzzyME.getLengthOf(mpk), schemeFuzzyME.getLengthOf(msk), schemeFuzzyME.getLengthOf(ek_S_A),  									\
		schemeFuzzyME.getLengthOf(dk_SBPA), schemeFuzzyME.getLengthOf(CT)																	\
	]
	del schemeFuzzyME
	print("Original:", message)
	print("Decrypted:", M)
	print("Is the scheme correct (message == M)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, n, d, round if isinstance(round, int) else None] + booleans + timeRecords + spaceRecords

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
	roundCount, filePath = 1, "SchemeFuzzyME.xlsx"
	queries = ["curveType", "secparam", "n", "d", "roundCount"]
	validators = ["isSystemValid", "isSchemeCorrect"]
	metrics = 	[															\
		"Setup (s)", "EKGen (s)", "DKGen (s)", "Encryption (s)", "Decryption (s)", 	\
		"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 			\
		"mpk (B)", "msk (B)", "ek_S_A (B)", "dk_SBPA (B)", "CT (B)"				\
	]
	
	# Scheme #
	qLength, columns, results = len(queries), queries + validators + metrics, []
	length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
	try:
		for curveType in curveTypes:
			for n in range(10, 31, 5):
				for d in range(5, n, 5):
					average = Scheme(curveType, n = n, d = d, round = 0)
					for round in range(1, roundCount):
						result = Scheme(curveType, n = n, d = d, round = round)
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
	iRet = EXIT_SUCCESS if results and all(all(tuple(r == roundCount for r in result[qLength:qvLength]) + tuple(r > 0 for r in result[qvLength:length])) for result in results) else EXIT_FAILURE
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