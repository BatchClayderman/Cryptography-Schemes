import os
from sys import argv, exit
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
	def __init__(self, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
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
	def Setup(self:object) -> tuple: # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Scheme #
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		g = self.__group.random(G1) # generate $g \in \mathbb{G}_1$ randomly
		h = self.__group.random(G1) # generate $h \in \mathbb{G}_1$ randomly
		x, alpha = self.__group.random(ZR), self.__group.random(ZR) # generate $x, \alpha \in \mathbb{Z}_p^*$ randomly
		H1 = lambda x:self.__group.hash(self.__group.serialize(x), G1) $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(self.__group.serialize(x), G1) $H_2: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H3 = lambda x:self.__group.hash(self.__group.serialize(x), ZR) $H_3: \{0, 1\}^* \rightarrow \mathbb{Z}_p^*$
		H4 = lambda x:self.__group.hash(self.__group.serialize(x), GT) $H_4: \{0, 1\}^* \rightarrow \mathbb{G}_T$
		H5 = lambda x:self.__group.hash(self.__group.serialize(x), G1) $H_5: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H6 = lambda x:self.__group.hash(self.__group.serialize(x), G1) $H_6: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H7 = lambda x:self.__group.hash(self.__group.serialize(x), G1) $H_7: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		y = g ** x # $y \gets g^x$
		self.__mpk = (g, h, H1, H2, H3, H4, H5, H6, H7, y) # $ \textit{mpk} \gets (G, G_T, q, g, e, h, H_1, H_2, H_3, H_4, H_5, H_6, H_7, y)$
		self.__msk = (x, alpha) # $\textit{msk} \gets (x, \alpha)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # $\textbf{return }(\textit{mpk}, \textit{msk})$
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
		H1 = self.__mpk[2]
		x, alpha = self.__msk
		
		# Scheme #
		dk_id_R1 = H1(id_R) ** x # $\textit{dk}_{\textit{id}_R, 1} \gets H_1(\textit{id}_R)^x$
		dk_id_R2 = H1(id_R) ** alpha # $\textit{dk}_{\textit{id}_R, 1} \gets H_1(\textit{id}_R)^\alpha$
		dk_id_R = (dk_id_R1, dk_id_R2) # $\textit{dk}_{\textit{id}_R} \gets (\textit{dk}_{\textit{id}_R, 1}, \textit{dk}_{\textit{id}_R, 2})$
		
		# Return #
		return dk_id_R # $\textbf{return }\textit{dk}_{\textit{id}_R}$
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
		H2 = self.__mpk[3]
		alpha = self.__msk[-1]
		
		# Scheme #
		ek_id_S = H2(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_2(\textit{id}_S)^\alpha$
		
		# Return #
		return ek_id_S # $\textbf{return }\textit{ek}_{\textit{id}_S}$
	def ReEKGen(self:object, ekid2:Element, dkid2:tuple, id1:Element, id3:Element) -> tuple: # $\textbf{ReEKGen}(\textit{ek}_{\textit{id}_2}, \textit{dk}_{\textit{id}_2}, \textit{id}_1, \textit{id}_3) \rightarrow \textit{rk}$
		# Check #
		if not self.__flag:
			print("ReEKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ReEKGen`` subsequently. ")
			self.Setup()
		if isinstance(ekid2, Element): # type check
			ek_id_2 = ekid2
		else:
			ek_id_2 = self.EKGen(self.__group.random(ZR))
			print("ReEKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(dkid2, tuple) and len(dkid2) == 2 and all([isinstance(ele, Element) for ele in dkid2]): # hybrid check
			dk_id_2 = dkid2
		else:
			dk_id_2 = self.DKGen(self.__group.random(ZR))
			print("ReEKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(id1, Element) and id1.type == ZR: # type check
			id_1 = id1
		else:
			id_1 = self.__group.random(ZR)
			print("ReEKGen: The variable $\\textit{id}_1$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		if isinstance(id3, Element) and id3.type == ZR: # type check
			id_3 = id3
		else:
			id_3 = self.__group.random(ZR)
			print("ReEKGen: The variable $\\textit{id}_3$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1, H2, H6, H7, y = self.__mpk[2], self.__mpk[3], self.__mpk[7], self.__mpk[8], self.__mpk[-1]
		
		# Scheme #
		N = self.__group.random(ZR) # generate $N \in \{0, 1\}^\lambda$ randomly
		xBar = self.__group.random(ZR) # generate $\bar{x} \in \mathbb{Z}_p^*$ randomly
		rk1 = g ** xBar # $\textit{rk}_1 \gets g^{\bar{x}}$
		rk2 = dk_id_2[0] * h ** xBar * H6(pair(y, H1(id_3)) ** xBar) # $\textit{rk}_2 \gets \textit{dk}_{\textit{id}_2, 1} h^{\bar{x}} H_6(e(y, H_1(\textit{id}_3))^{\bar{x}})$
		K = pair(ek_id_2, H1(id_3)) # $K \gets e(\textit{ek}_{\textit{id}_2}, H_1(\textit{id}_3))$
		rk3 = pair(H2(id_1), H7(K + id_2 + id_3 + N) * dk_id_2[1]) # $\textit{rk}_3 \gets e(H_2(\textit{id}_1), H_7(K || \textit{id}_2 || \textit{id}_3 || N) \cdot \textit{dk}_{\textit{id}_2, 2})$
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
		if isinstance(id2, Element) and id2.type == ZR: # type check
			id_2 = id2
		else:
			id_2 = self.__group.random(ZR)
			print("Enc: The variable $\\textit{id}_2$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			m = message
		else:
			m = self.__group.random(GT)
			print("Enc: The variable $M$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, h, H1, H3, H4, H5 = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[4], self.__mpk[5], self.__mpk[6]
		
		# Scheme #
		sigma = self.__group.random(G1) # generate $\sigma \in \mathbb{G}_1$ randomly
		eta = self.__group.random(GT) # generate $\eta \in \mathbb{G}_T$ randomly
		r = H3(m + sigma + eta) # $r \gets H_3(m || \sigma || \eta)$
		ct1 = h ** r # $\textit{ct}_1 \gets h^r$
		ct2 = g ** r # $\textit{ct}_2 \gets g^r$
		ct3 = (m + sigma) ^ H4(pair(y, H1(id_2)) ** r) ^ H4(eta) # $\textit{ct}_3 \gets (m || \sigma) \oplus H_4(e(y, H_1(\textit{id}_2))^r) \oplus H_4(\eta)$
		ct4 = eta * pair(ek_id_1, H1(id_2)) # $\textit{ct}_4 \gets \eta \cdot e(\textit{ek}_{\textit{id}_1}, H_1(\textit{id}_2))$
		ct5 = H5(ct1 + ct2 + ct3 + ct4) ** r # $\textit{ct}_5 \gets H_5(\textit{ct}_1 || \textit{ct}_2 || \textit{ct_3} || \textit{ct}_4)^r$
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
			rk = self.ReEKGen(self.EKGen(id2Generated), self.DKGen(id2Generated), self.__group.random(ZR), self.__group.random(ZR))
			print("ReEnc: The variable $\\textit{rk}$ should be a tuple containing 4 elements but it is not, which has been generated randomly. ")
		del id2Generated
		
		# Unpack #
		g, h, H1, H2, H6, H7, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[7], self.__mpk[8], self.__mpk[-1]
		x = self.__msk[0]
		rk1, rk2, rk3 = rk[1], rk[2], rk[3]
		ct1, ct2, ct3, ct4, ct5 = ct
		
		# Scheme #
		if pair(ct1, g) == pair(h, ct2) and pair(ct1, H5(ct1 + ct2 + ct3 + ct4)) == pair(h, ct5):
			ct4Prime = ct4 / rk3 # $\textit{ct}_4' \gets \frac{\textit{ct}_4}{\textit{rk}_3}$
			ct7 = pair(rk2, ct2) / pair(ct1, rk1) # $\textit{ct}_7 \gets \frac{e(\textit{rk}_2, \textit{ct}_2)}{e(\textit{ct}_1, \textit{rk}_1)}$
			ctPrime = (ct2, ct3, ct4Prime, ct6, ct7, N) # $\textit{ct}' \gets (\textit{ct}_2, \textit{ct}_3, \textit{ct}_4', \textit{ct}_6, \textit{ct}_7, N)$
		else:
			ctPrime = False
		
		# Return #
		return ctPrime # $\textbf{return }\textit{ct}'$
	def Dec(self:object, skIDk:tuple, cipher:tuple) -> bytes: # $\textbf{Dec}(\textit{CT}, \textit{sk}_{\textit{ID}_k}) \rightarrow M$
		# Check #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if isinstance(skIDk, tuple) and 9 <= len(skIDk) <= ((self.__l - 1) << 2) + 5 and all([isinstance(ele, Element) for ele in skIDk]): # hybrid check
			sk_ID_k = skIDk
		else:
			sk_ID_k = self.KGen(tuple(self.__group.random(ZR) for i in range(self.__l - 1)))
			print("Dec: The variable $\\textit{{ID}}_k$ should be a tuple containing $k = \\|\\textit{{ID}}_k\\|$ elements where the integer $k \\in [9, {0}]$ but it is not, which has been generated randomly with a length of $9$. ".format(5 + ((self.__l - 1) << 2)))
		if isinstance(cipher, tuple) and len(cipher) == 4 and all([isinstance(ele, Element) for ele in cipher]):# hybrid check
			CT = cipher
		else:
			CT = self.Enc(tuple(self.__group.random(ZR) for i in range(self.__l - 1)), self.__group.random(GT))
			print("Dec: The variable $\\textit{CT}$ should be a tuple containing 4 elements but it is not, which has been generated with $M \\in \\mathbb{G}_T$ generated randomly. ")
		
		# Unpack #
		A, B, C, D = CT
		a0, a1, b = sk_ID_k[0], sk_ID_k[1], sk_ID_k[2]
		
		# Scheme #
		M = pair(b, D) * A / (pair(B, a0) * pair(C, a1)) # $M \gets \cfrac{e(b, D) \cdot A}{e(B, a_0) \cdot e(C, a_1)}$
		
		# Return #
		return M # $\textbf{return }M$
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


def Scheme(curveType:tuple|list|str, l:int, k:int, round:int = None) -> list:
	# Begin #
	if isinstance(l, int) and isinstance(k, int) and 2 <= k < l:
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
			print("l =", l)
			print("k =", k)
			if isinstance(round, int) and round >= 0:
				print("round =", round)
			print("Is the system valid? No. \n\t{0}".format(e))
			return (																																														\
				([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [(curveType if isinstance(curveType, str) else None), None])		\
				+ [l, k, round if isinstance(round, int) and round >= 0 else None] + [False] * 3 + [-1] * 19																													\
			)
	else:
		print("Is the system valid? No. The parameters $l$ and $k$ should be two positive integers satisfying $2 \\leqslant k < l$. ")
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [(curveType if isinstance(curveType, str) else None), None])		\
			+ [l if isinstance(l, int) else None, k if isinstance(k, int) else None, round if isinstance(round, int) and round >= 0 else None] + [False] * 3 + [-1] * 19																	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	print("l =", l)
	print("k =", k)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBPME = SchemeIBPME(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBPME.Setup(l)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# KGen #
	startTime = perf_counter()
	ID_k = tuple(group.random(ZR) for i in range(k))
	sk_ID_k = schemeIBPME.KGen(ID_k)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DerivedKGen #
	startTime = perf_counter()
	sk_ID_kMinus1 = schemeIBPME.KGen(ID_k[:-1]) # remove the last one to generate the sk_ID_kMinus1
	sk_ID_kDerived = schemeIBPME.DerivedKGen(sk_ID_kMinus1, ID_k)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = group.random(GT)
	CT = schemeIBPME.Enc(ID_k, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec #
	startTime = perf_counter()
	M = schemeIBPME.Dec(sk_ID_k,  CT)
	MDerived = schemeIBPME.Dec(sk_ID_kDerived, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	spaceRecords = [																																													\
		schemeIBPME.getLengthOf(group.random(ZR)), schemeIBPME.getLengthOf(group.random(G1)), schemeIBPME.getLengthOf(group.random(G2)), schemeIBPME.getLengthOf(group.random(GT)), 	\
		schemeIBPME.getLengthOf(mpk), schemeIBPME.getLengthOf(msk), schemeIBPME.getLengthOf(sk_ID_k), schemeIBPME.getLengthOf(sk_ID_kDerived), schemeIBPME.getLengthOf(CT)	\
	]
	del schemeIBPME
	print("Original:", message)
	print("Derived:", MDerived)
	print("Decrypted:", M)
	print("Is the deriver passed (message == M')? {0}. ".format("Yes" if message == MDerived else "No"))
	print("Is the scheme correct (message == M)? {0}. ".format("Yes" if message == M else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, l, k, round if isinstance(round, int) else None, True, message == MDerived, message == M] + timeRecords + spaceRecords

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
	curveTypes = ("MNT159", "MNT201", "MNT224", ("SS512", 512))
	roundCount, filePath = 20, "SchemeIBPME.xlsx"
	columns = [																	\
		"curveType", "secparam", "l", "k", "roundCount", 								\
		"isSystemValid", "isDeriverPassed", "isSchemeCorrect", 							\
		"Setup (s)", "KGen (s)", "DerivedKGen (s)", "Enc (s)", "Dec (s)", 					\
		"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 		\
		"mpk (B)", "msk (B)", "SK (B)", "SK' (B)", "CT (B)"								\
	]
	
	# Scheme #
	length, results = len(columns), []
	try:
		roundCount = max(1, roundCount)
		for curveType in curveTypes:
			for l in (5, 10, 15, 20, 25, 30):
				for k in range(5, l, 5):
					average = Scheme(curveType, l, k, 0)
					for round in range(1, roundCount):
						result = Scheme(curveType, l, k, round)
						for idx in range(5, 8):
							average[idx] += result[idx]
						for idx in range(8, length):
							average[idx] = -1 if average[idx] < 0 or result[idx] < 0 else average[idx] + result[idx]
					average[4] = roundCount
					for idx in range(8, length):
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