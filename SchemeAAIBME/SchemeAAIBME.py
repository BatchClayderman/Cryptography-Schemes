import os
from sys import argv, exit
from random import shuffle
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


class SchemeAAIBME:
	def __init__(self, group:None|PairingGroup = None) -> object: # This scheme is only applicable to symmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
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
		alpha, beta, t1, t2, t3, t4 = self.__group.random(ZR, 6) # generate $\alpha, \beta, t_1, t_2, t_3, t_4 \in \mathbb{Z}_r$ randomly
		g2, g3 = self.__group.random(G1), self.__group.random(G1) # generate $g_2, g_3 \in \mathbb{G}_1$ randomly
		TVec = tuple(self.__group.random(G1) for i in range(n + 1)) # generate $\bm{T} \gets (\bm{T}_0, \bm{T}_1, \cdots, \bm{T}_n) \in \mathbb{G}_1^{n + 1}$ randomly
		TPrimeVec = tuple(self.__group.random(G1) for i in range(n + 1)) # generate $\bm{T}' \gets (\bm{T}'_0, \bm{T}'_1, \cdots, \bm{T}'_n) \in \mathbb{G}_1^{n + 1}$ randomly
		uVec = tuple(self.__group.random(G1) for i in range(n + 1)) # generate $\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n) \in \mathbb{G_1}^{n + 1}$ randomly
		uPrimeVec = tuple(self.__group.random(G1) for i in range(n + 1)) # generate $\bm{u}' \gets (\bm{u}'_0, \bm{u}'_1, \cdots, \bm{u}'_n) \in \mathbb{G}_1^{n + 1}$ randomly
		H1 = lambda x:self.__group.hash(self.__group.serialize(x), G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		g1 = g ** alpha # $g_1 \gets g^\alpha$
		g1Prime = g ** beta # $g'_1 \gets g^\beta$
		Y1 = pair(g1, g2) ** (t1 * t2) # $Y_1 \gets e(g_1, g_2)^{t_1 t_2}$
		Y2 = pair(g3, g) ** beta # $Y_2 \gets e(g_3, g)^\beta$
		v1 = g ** t1 # $v_1 \gets g^{t_1}$
		v2 = g ** t2 # $v_2 \gets g^{t_2}$
		v3 = g ** t3 # $v_3 \gets g^{t_3}$
		v4 = g ** t4 # $v_4 \gets g^{t_4}$
		self.__mpk = (g1, g1Prime, g2, g3, Y1, Y2, v1, v2, v3, v4, uVec, TVec, uPrimeVec, TPrimeVec, H1) # $ \textit{mpk} \gets (g_1, g'_1, g_2, g_3, Y_1, Y_2, v_1, v_2, v_3, v_4, \bm{u}, \bm{T}, \bm{u}', \bm{T}', H_1)$
		self.__msk = (g2 ** alpha, beta, t1, t2, t3, t4) # $\textit{msk} \gets (g_2^\alpha, \beta, t_1, t_2, t_3, t_4)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # $\textbf{return }(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, IDA:tuple) -> tuple: # $\textbf{EKGen}(\textit{ID}_A) \rightarrow \textit{ek}_{\textit{ID}_A}$
		# Check #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDA, tuple) and len(IDA) == self.__n and all([isinstance(ele, Element) and ele.type == ZR for ele in IDA]): # hybrid check
			ID_A = IDA
		else:
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("EKGen: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g3, uVec, TVec = self.__mpk[3], self.__mpk[10], self.__mpk[11]
		beta = self.__msk[1]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		H = lambda vec, ID:vec[0] * self.__product(		\
			vec[j + 1] ** ID[j] for j in range(self.__n)	\
		) # $H: \bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n) \rightarrow \bm{u}_0\prod\limits_{j \in [1, n]} \bm{u}_j^{\textit{ID}_j}$
		rVec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{r} = (r_1, r_2, \cdots, r_n) \in \mathbb{Z}_r^n$ randomly
		coefficients = (beta, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		q = lambda x:self.__computePolynomial(x, coefficients) # generate a $(d - 1)$ degree polynominal $q(x)$ s.t. $q(0) = \beta$ randomly
		ek_ID_A = list((g3 ** q(self.__group.init(ZR, i)) * (H(uVec, ID_A) * TVec[i]) ** rVec[i], g ** rVec[i]) for i in range(self.__n)) # $\textit{ek}_{\textit{ID}_{A_i}} \gets (g_3^{q(i)} [H(\bm{u}', \textit{ID}_A)T'_i]^{r_i}, g^{r_i}), \forall i \in \{1, 2, \cdots, n\}$
		shuffle(ek_ID_A)
		ek_ID_A = tuple(ek_ID_A[self.__d:]) # generate $\textit{ek}_{\textit{ID}_A}(S) \subset \textit{ek}_{\textit{ID}_A}$ s.t. $\|\textit{ek}_{\textit{ID}_A}(S)\| = d$ randomly
		
		# Return #
		return ek_ID_A # \textbf{return} $\textit{ek}_{\textit{ID}_A}(S)$
	def DKGen(self:object, IDB:tuple) -> tuple: # $\textbf{DKGen}(\textit{id}_B) \rightarrow \textit{dk}_{\textit{ID}_B}$
		# Check #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDB, tuple) and len(IDB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDB): # hybrid check
			ID_B = IDB
		else:
			ID_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("DKGen: The variable $\\textit{ID}_B$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g2, uVec, TVec = self.__mpk[2], self.__mpk[10], self.__mpk[11]
		g2ToThePowerOfAlpha, t1, t2, t3, t4 = self.__mpk[0], self.__msk[2], self.__msk[3], self.__msk[4], self.__msk[5]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		H = lambda vec, ID:vec[0] * self.__product(		\
			vec[j + 1] ** ID[j] for j in range(self.__n)	\
		) # $H: \bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n) \rightarrow \bm{u}_0\prod\limits_{j \in [1, n]} \bm{u}_j^{\textit{ID}_j}$
		k1Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{k}_1 = (k_{1, 1}, k_{1, 2}, \cdots, k_{1, n}) \in \mathbb{Z}_r^n$ randomly
		k2Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{k}_2 = (k_{2, 1}, k_{2, 2}, \cdots, k_{2, n}) \in \mathbb{Z}_r^n$ randomly
		dk_ID_B = list( # $\textit{dk}_{\textit{ID}_{B_i}} \gets (
			(
				g ** (k1Vec[i] * t1 * t2 + k2Vec[i] * t3 * t4), # g^{k_{1, i} t_1 t_2 + k_{2, i} t_3 t_4}
				g2ToThePowerOfAlpha ** (-t2) * (H(uVec, ID_B) * TVec[i]) ** (-k1Vec[i] * t2), # g_2^{-\alpha t_2} [H(\bm{u}, \textit{ID}_B) T_i]^{k_{1, i} t_2}
				g2ToThePowerOfAlpha ** (-t1) * (H(uVec, ID_B) * TVec[i]) ** (-k1Vec[i] * t1), # g_2^{-\alpha t_1} [H(\bm{u}, \textit{ID}_B) T_i]^{k_{1, i} t_1}
				(H(uVec, ID_B) * TVec[i]) ** (-k2Vec[i] * t4), # [H(\bm{u}, \textit{ID}_B) T_i]^{k_{2, i} t_4}
				(H(uVec, ID_B) * TVec[i]) ** (-k2Vec[i] * t3) # [H(\bm{u}, \textit{ID}_B) T_i]^{k_{2, i} t_3}
			) for i in range(self.__n) # ), \forall i \in \{1, 2, \cdots, n\}
		) # $
		shuffle(dk_ID_B)
		dk_ID_B = tuple(dk_ID_B[self.__d:]) # generate $\textit{dk}_{\textit{ID}_B}(S') \subset \textit{dk}_{\textit{ID}_B}$ s.t. $\|\textit{dk}_{\textit{ID}_B}(S')\| = d$ randomly
		
		# Return #
		return dk_ID_B # \textbf{return} $\textit{dk}_{\textit{ID}_B}(S')$
	def Enc(self:object, ekIDA:tuple, IDA:tuple, IDB:tuple, message:Element) -> tuple: # $\textbf{Enc}(\textit{ek}_{\textit{ID}_A}, \textit{ID}_A, \textit{ID}_B, M) \rightarrow \textit{CT}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(IDA, tuple) and len(IDA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDA): # hybrid check
			ID_A = IDA
			if isinstance(ekIDA, tuple) and len(ekIDA) == self.__n and all(isinstance(ele[0], tuple) and isinstance(ele[1], tuple) and len(ele[0]) == len(ele[1]) == 2 for ele in ekIDA): # hybrid check
				ek_ID_A = ekIDA
			else:
				ek_ID_A = self.EKGen(ID_A)
				print("Enc: The variable $\\textit{ek}_{\textit{ID}_A}$ should be a tuple containing $n$ tuples but it is not, which has been generated accordingly. ")
		else:
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Enc: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			ek_ID_A = self.EKGen(ID_A)
			print("Enc: The variable $\\textit{ek}_{\\textit{ID}_A}$ has been generated accordingly. ")
		if isinstance(IDB, tuple) and len(IDB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDB): # hybrid check
			ID_B = IDB
		else:
			ID_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Enc: The variable $\\textit{ID}_B$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			M = message
		else:
			M = self.__group.random(GT)
			print("Enc: The variable $M$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		Y1, Y2, v1, v2, v3, v4, uVec, TVec = self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[9], self.__mpk[10], self.__mpk[11]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		H = lambda vec, ID:vec[0] * self.__product(		\
			vec[j + 1] ** ID[j] for j in range(self.__n)	\
		) # $H: \bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n) \rightarrow \bm{u}_0\prod\limits_{j \in [1, n]} \bm{u}_j^{\textit{ID}_j}$
		SPrimePrime = list(range(self.__n))
		shuffle(SPrimePrime)
		SPrimePrime = tuple(SPrimePrime[:self.__d]) # generate $S'' \subset [1, n]$ s.t. $\|S''\| = d$ randomly
		s = self.__group.random(ZR) # generate $s \in \mathbb{Z}_r$ randomly
		s1Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{s}_1 = (s_{1, 1}, s_{1, 2}, \cdots, s_{1, n})$ randomly
		s2Vec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{s}_2 = (s_{2, 1}, s_{2, 2}, \cdots, s_{2, n})$ randomly
		coefficients = (s, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		q = lambda x:self.__computePolynomial(x, coefficients) # generate a $(d - 1)$ degree polynominal $q(x)$ s.t. $q(0) = s$ randomly
		K_s = Y1 ** s # $K_s \gets Y_1^s$
		K_l = Y2 ** s # $K_l \gets Y_2^s$
		C = M * K_s * K_l # $C \gets M \cdot K_s \cdot K_l$
		C1Vec = tuple((H(uVec, ID_B) * TVec[i]) ** q(self.__group.init(ZR, i)) for i in SPrimePrime) # $C_{1, i} \gets [H(\bm{u}, \textit{ID}_B) T_i]^{q(i)}, \forall i \in S''$
		C2Vec = tuple(v1 ** (q(self.__group.init(ZR, i)) - s1Vec[i]) for i in SPrimePrime) # $C_{2, i} \gets v_1^{q(i) - s_{1, i}}, \forall i \in S''$
		C3Vec = tuple(v2 ** s1Vec[i] for i in SPrimePrime) # $C_{3, i} \gets v_2^{s_{1, i}}, \forall i \in S''$
		C4Vec = tuple(v3 ** (q(self.__group.init(ZR, i)) - s2Vec[i]) for i in SPrimePrime) # $C_{4, i} \gets v_3^{q(i) - s_{2, i}}, \forall i \in S''$
		C5Vec = tuple(v4 ** s2Vec[i] for i in SPrimePrime) # $C_{5, i} \gets v_4^{s_{2, i}}, \forall i \in S''$
		zVec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{z} = (z_1, z_2, \cdots, z_n)$ randomly
		zPrimeVec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{z}' = (z'_1, z'_2, \cdots, z'_n)$ randomly
		C6Vec = tuple(g ** zPrimeVec[i] for i in S) # $C_{6, i} \gets g^{z'_i}, \forall i \in S$
		C7Vec = tuple((ek_ID_A[i][1] * g ** zVec[i]) ** s for i in S) # $C_{7, i} \gets (\textit{ek}_{\textit{ID}_{A_{i, 2}}}(S) \cdot g^{z_i})^s, \forall i \in S$
		C8Vec = tuple(ek_ID_A[i][0] ** s * (H(uPrimeVec, ID_A) * TPrimeVec[i]) ** (s * zVec[i]) * H1( # $C_{8, i} \gets \textit{ek}_{\textit{ID}_{A_{i, 1}}}(S) \cdot [H(\bm{u}', \textit{ID}_A) T'_i]^{s \cdot z_i} \cdot H_1(
			self.__group.serialize(C) + self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) # C || C_{1, i} || C_{2, i} || C_{3, i}
			+ self.__group.serialize(C4Vec[i]) + self.__group.serialize(C5Vec[i]) + self.__group.serialize(C6Vec[i]) + self.__group.serialize(C7Vec[i]) # C_{4, i} || C_{5, i} || C_{6, i} || C_{7, i}
		) for i in S) # ), \forall i \in S$
		CT = (SPrimePrime, IStar, C, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec, C6Vec, C7Vec, C8Vec) # $\textit{CT} \gets (S'', I^*, C, \vec{C}_1, \vec{C}_2, \vec{C}_3, \vec{C}_4, \vec{C}_5, \vec{C}_6, \vec{C}_7, \vec{C}_8)$
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Dec(self:object, dkSBPA:tuple, SA:tuple, PA:tuple, SB:tuple, PB:tuple, cipherText:tuple) -> Element|bool: # $\textbf{Dec}(\textit{dk}_{S_B, P_A}, S_B, P_A, \textit{CT}) \rightarrow M$
		# Check #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if (																																	\
			isinstance(SA, tuple) and isinstance(PA, tuple) and isinstance(SB, tuple) and isinstance(PB, tuple) and len(SA) == len(PA) == len(SA) == len(SB) == self.__n	\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in SA) and all(isinstance(ele, Element) and ele.type == ZR for ele in PA)						\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in SB) and all(isinstance(ele, Element) and ele.type == ZR for ele in PB)						\
		): # hybrid check
			ID_A, P_A, S_B, P_B = SA, PA, SB, PB
			if (																																		\
				isinstance(dkSBPA, tuple) and len(dkSBPA) == 2 and isinstance(dkSBPA[0], tuple) and isinstance(dkSBPA[1], tuple) and len(dkSBPA[0]) == len(dkSBPA[1]) == 5	\
				and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in dkSBPA[0]) and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in dkSBPA[1])				\
			): # hybrid check
				dk_SBPA = dkSBPA
			else:
				dk_SBPA = self.DKGen(S_B, P_A)
				print("Dec: The variable $\\textit{dk}_{S_B, P_A}$ should be a tuple containing 2 tuples but it is not, which has been generated accordingly. ")
		else:
			ID_A, P_A = tuple(self.__group.random(ZR) for _ in range(self.__n)), tuple(self.__group.random(ZR) for _ in range(self.__n))
			S_B, P_B = tuple(self.__group.random(ZR) for _ in range(self.__n)), tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Dec: Each of the variables $ID_A$, $P_A$, $S_B$, and $P_B$ should be a tuple containing 4 elements of $\\mathbb{Z}_r$ but at least one of them is not, all of which have been generated randomly. ")
			dk_SBPA = self.DKGen(S_B, P_A)
			print("Dec: The variable $\\textit{dk}_{S_B, P_A}$ has been generated accordingly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 10 and all(isinstance(ele, Element) for ele in cipherText[:5]) and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in cipherText[5:]): # hybrid check
			CT = cipherText
		else:
			CT = self.Enc(self.EKGen(ID_A), ID_A, P_B, self.__group.random(GT))
			print("Dec: The variable $\\textit{CT}$ should be a tuple containing 5 elements and 5 tuples but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[11]
		dk_S_B, dk_P_A = dk_SBPA
		dk_S_B_0, dk_S_B_1, dk_S_B_2, dk_S_B_3, dk_S_B_4 = dk_S_B
		dk_P_A_0, dk_P_A_1, dk_P_A_2, dk_P_A_3, dk_P_A_4 = dk_P_A
		C0, C1, C2, C3, C4, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec = CT
		
		# Scheme #
		WAPrime = set(ID_A).intersection(P_A) # $W'_A \gets ID_A \cap P_A$
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
					) ** Delta(ID_A[i], WA, 0) for i in range(self.__n)																																			\
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
	schemeAAIBME = SchemeAAIBME(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeAAIBME.Setup(n = n, d = d)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# EKGen #
	startTime = perf_counter()
	ID_A = tuple(group.random(ZR) for _ in range(n))
	ek_ID_A = schemeAAIBME.EKGen(ID_A)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DKGen #
	startTime = perf_counter()
	ID_B = tuple(group.random(ZR) for _ in range(n))
	dk_ID_B = schemeAAIBME.DKGen(ID_B)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = group.random(GT)
	CT = schemeAAIBME.Enc(ek_ID_A, ID_A, ID_B, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec #
	startTime = perf_counter()
	M = schemeAAIBME.Dec(dk_SBPA, ID_A, P_A, S_B, P_B, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(M, bool) and message == M]
	spaceRecords = [																														\
		schemeAAIBME.getLengthOf(group.random(ZR)), schemeAAIBME.getLengthOf(group.random(G1)), schemeAAIBME.getLengthOf(group.random(GT)), 	\
		schemeAAIBME.getLengthOf(mpk), schemeAAIBME.getLengthOf(msk), schemeAAIBME.getLengthOf(ek_ID_A),  									\
		schemeAAIBME.getLengthOf(dk_ID_B), schemeAAIBME.getLengthOf(CT)																	\
	]
	del schemeAAIBME
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
	roundCount, filePath = 100, "SchemeAAIBME.xlsx"
	queries = ["curveType", "secparam", "n", "d", "roundCount"]
	validators = ["isSystemValid", "isSchemeCorrect"]
	metrics = 	[															\
		"Setup (s)", "EKGen (s)", "DKGen (s)", "Enc (s)", "Dec (s)", 	\
		"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 			\
		"mpk (B)", "msk (B)", "ek_ID_A (B)", "dk_ID_B (B)", "CT (B)"			\
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