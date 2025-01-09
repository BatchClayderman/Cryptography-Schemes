import os
from sys import argv, exit
from time import perf_counter, sleep
try:
	from psutil import Process
except:
	print("Cannot compute the memory via ``psutil.Process``. ")
	print("Please try to install the ``psutil`` library via ``python -m pip install psutil`` or ``apt-get install python3-psutil``. ")
	print("Please press the enter key to exit. ")
	input()
	exit(-1)
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element
	from charm.toolbox.matrixops import GaussEliminationinGroups
except:
	print("The environment of the ``charm`` library is not handled correctly. ")
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


class SchemeIBMECH:
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		super().__init__()
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__operand = (1 << self.__group.secparam) - 1 # use to cast binary strings
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def __product(self:object, vec:tuple|list|set) -> Element:
		if isinstance(vec, (tuple, list, set)) and vec and all([isinstance(ele, Element) for ele in vec]):
			element = vec[0]
			for ele in vec[1:]:
				element *= ele
			return element
		else:
			return self.__group.init(ZR, 1)
	def Setup(self:object): # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Scheme #
		g1 = self.__group.random(G1) # generate $g_1 \in \mathbb{G}_1$ randomly
		g2 = self.__group.random(G2) # generate $g_2 \in \mathbb{G}_2$ randomly
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		alpha, eta = self.__group.random(ZR), self.__group.random(ZR) # generate $\alpha, \eta \in \mathbb{Z}_p^*$ randomly
		zero, one = self.__group.init(ZR, 0), self.__group.random(ZR) # generate $\textbf{0}_{\mathbb{Z}_p^*}, \textbf{1}_{\mathbb{Z}_p^*} \in \mathbb{Z}_p^*$ randomly
		B = [[self.__group.random(ZR) for j in range(8)] for i in range(8)] # generate $\bm{B} \gets (\mathbb{Z}_p^*)^{8 \times 8}$ randomly
		D = tuple(tuple(g1 ** B[i][j] for j in range(8)) for i in range(4)) # $\mathbb{D}_{i, j} \gets g_1^{\bm{B}_{i, j}}, \forall i \in \{1, 2, 3, 4\}, \forall j \in \{1, 2, \cdots, 8\}$
		DStar = tuple(tuple(GaussEliminationinGroups([B[j] + [one if i == j else zero] for j in range(8)])) for i in range(4)) # $\mathbb{D}_i^* \gets \textit{GaussEliminationinGroups}(\bm{B} || [1 = i, 2 = i, \cdots, 8 = i]^\mathrm{T}), \forall i \in \{1, 2, 3, 4\}$
		del B
		gT = pair(g1, g2) # $g_T \gets e(g_1, g_2)$
		self.__mpk = (gT ** (alpha * one), gT ** (eta * one), D[0], D[1]) # $\textit{mpk} \gets (g_T^{\alpha \times \textbf{1}_{\mathbb{Z}_p^*}}, g_T^{\eta \times \textbf{1}_{\mathbb{Z}_p^*}}, D_1, D_2)$
		self.__msk = (alpha, eta, g1, g2, D[2], D[3], DStar[0], DStar[1], DStar[2], DStar[3]) # $\textit{msk} \gets (\alpha, \eta, g_1, g_2, \bm{d}_3, \bm{d}_4, \bm{d}_1^*, \bm{d}_2^*, \bm{d}_3^*, \bm{d}_4^*)$
		
		# Return #
		self.__flag = True
		return (self.__mpk, self.__msk) # $\textbf{return }(\textit{mpk}, \textit{msk})$
	def SKGen(self:object, sender:Element) -> tuple: # $\textbf{SKGen}(\sigma) \rightarrow \textit{ek}_\sigma$
		# Check #
		if not self.__flag:
			print("SKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``SKGen`` subsequently. ")
			self.Setup()
		if isinstance(sender, Element) and sender.type == ZR: # type check
			sigma = sender
		else:
			sigma = self.__group.random(ZR)
			print("SKGen: The variable $\\sigma$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		eta, d3, d4 = self.__msk[1], self.__msk[4], self.__msk[5]
		
		# Scheme #
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_p^*$
		ek_sigma = tuple(d3[i] ** (eta + r * sigma) / d4[i] ** r for i in range(8)) # $\textit{ek}_\sigma \gets \frac{\bm{d}_{3, i}^{\eta + r \sigma}}{\bm{d}_{4, i}^r}, \forall i \in \{1, 2, \cdots, 8\}$
		
		# Return #
		return ek_sigma # $\textbf{return }\textit{ek}_\sigma$
	def RKGen(self:object, receiver:Element) -> tuple: # $\textbf{RKGen}(\rho) \rightarrow \textit{dk}_\rho$
		# Check #
		if not self.__flag:
			print("RKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``RKGen`` subsequently. ")
			self.Setup()
		if isinstance(receiver, Element) and receiver.type == ZR: # type check
			rho = receiver
		else:
			rho = self.__group.random(ZR)
			print("RKGen: The variable $\\rho$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		gTToThePowerOfEta = self.__mpk[1]
		alpha, g2, DStar1, DStar2, DStar3, DStar4 = self.__msk[0], self.__msk[3], self.__msk[6], self.__msk[7], self.__msk[8], self.__msk[9]
		
		# Scheme #
		s, s1, s2 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $s, s_1, s_2 \in \mathbb{Z}_p^*$ randomly
		k1 = tuple(g2 ** (DStar1[i] * (alpha + s1 * rho) - s1 * DStar2[i] + s * DStar3[i]) for i in range(8)) # $k_1 \gets \{g_2^{\bm{d}_{1, i} \cdot (\alpha + s_1 \rho) - s_1 \bm{d}_{2, i} + s \bm{d}_{3, i}}, \forall i \in \{1, 2, \cdots, 8\}\}$
		k2 = tuple(g2 ** (s2 * (rho * DStar1[i] - DStar2[i]) + s * DStar4[i]) for i in range(8)) # $k_2 \gets \{g_2^{s_2 \cdot (\rho * \bm{d}_{1, i} - \bm{d}_{2, i}) + s \bm{d}_{4, i}}, \forall i \in \{1, 2, \cdots, 8\}\}$
		k3 = gTToThePowerOfEta ** s # $k_3 \gets (g_T^\eta)^s$
		dk_rho = (k1, k2, k3) # $\textit{dk}_\rho \gets (k_1, k_2, k_3)$
		
		# Return #
		return dk_rho # $\textbf{return }\textit{dk}_\rho$
	def Enc(self:object, eksigma:tuple, receiver:Element, message:Element) -> tuple: # $\textbf{Enc}(\textit{ek}_\sigma, \textit{rcv}, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(eksigma, tuple) and len(eksigma) == 8 and all([isinstance(ele, Element) for ele in eksigma]): # hybrid check
			ek_sigma = eksigma
		else:
			ek_sigma = self.SKGen(self.__group.random(ZR))
			print("Enc: The variable $\\textit{ek}_\\sigma$ should be a tuple containing 8 elements but it is not, which has been generated randomly. ")
		if isinstance(receiver, Element) and receiver.type == ZR: # type check
			rcv = receiver
		else:
			rcv = self.__group.random(ZR)
			print("Enc: The variable $\\textit{rcv}$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			m = message
		else:
			m = self.__group.random(GT)
			print("Enc: The variable $m$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		gTToThePowerOfAlpha, D1, D2 = self.__mpk[0], self.__mpk[2], self.__mpk[3]
		
		# Scheme #
		z = self.__group.random(ZR) # generate $z \gets \mathbb{Z}_p^*$ randomly
		C = tuple(D1[i] ** z * D2[i] ** (z * rcv) * ek_sigma[i] for i in range(8)) # $C \gets \{\bm{d}_{1, i}^z \bm{d}_{2, i}^{z \cdot \textit{rcv}} \cdot (\textit{ek}_\sigma)_i, \forall i \in \{1, 2, \cdots, 8\}\}$
		C0 = gTToThePowerOfAlpha ** z * m # $C_0 \gets (g_T^\alpha)^z m$
		ct = (C, C0) # $\textit{ct} \gets (C, C_0)$
		
		# Return #
		return ct # $\textbf{return }\textit{ct}$
	def Dec(self:object, dkrho:tuple, sender:Element, cipher:tuple) -> Element: # $\textbf{Dec}(\textit{dk}_\rho, \textit{snd}, \textit{ct}) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if (																																\
			isinstance(dkrho, tuple) and len(dkrho) == 3 and isinstance(dkrho[0], tuple) and len(dkrho[0]) == 8 and all([isinstance(ele, Element) for ele in dkrho[0]])	\
			and isinstance(dkrho[1], tuple) and len(dkrho[1]) == 8 and all([isinstance(ele, Element) for ele in dkrho[1]]) and isinstance(dkrho[2], Element)			\
		): # hybrid check
			dk_rho = dkrho
		else:
			dk_rho = self.RKGen(self.__group.random(ZR))
			print("Dec: The variable $\\textit{dk}_\\rho$ should be a tuple containing 2 tuples and an element but it is not, which has been generated randomly. ")
		if isinstance(sender, Element) and sender.type == ZR: # type check
			snd = sender
		else:
			snd = self.__group.random(ZR)
			print("Dec: The variable $\\textit{snd}$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 2 and isinstance(cipher[0], tuple) and len(cipher[0]) == 8 and all([isinstance(ele, Element) for ele in cipher[0]]) and isinstance(cipher[1], Element): # hybrid check
			ct = cipher
		else:
			ct = self.Enc(self.SKGen(self.__group.random(ZR)), self.__group.random(ZR), self.__group.random(GT))
			print("Dec: The variable $\textit{ct}$ should be a tuple containing a tuple and an element but it is not, which has been generated randomly. ")
		
		# Unpack #
		k1, k2, k3 = dk_rho
		C, C0 = ct
				
		# Scheme #
		m = C0 * k3 / self.__product(tuple(pair(C[i], k1[i] * k2[i] ** snd) for i in range(8))) # $m \gets \frac{C_0 k_3}{\prod\limits_{i = 1}^8 e(C_i, k_{1, i} k_{2, i}^\textit{snd})}$
		
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
			+ [round if isinstance(round, int) else None] + [False] * 2 + [-1] * 19																																	\
		)
	process = Process(os.getpid())
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBMECH = SchemeIBMECH(group)
	timeRecords, memoryRecords = [], []

	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBMECH.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# SKGen #
	startTime = perf_counter()
	sigma = group.random(ZR)
	ek_sigma = schemeIBMECH.SKGen(sigma)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# RKGen #
	startTime = perf_counter()
	rho = group.random(ZR)
	dk_rho = schemeIBMECH.RKGen(rho)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Enc #
	startTime = perf_counter()
	message = group.random(GT)
	ct = schemeIBMECH.Enc(ek_sigma, rho, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Dec #
	startTime = perf_counter()
	m = schemeIBMECH.Dec(dk_rho, sigma, ct)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# End #
	sizeRecords = [																																									\
		schemeIBMECH.getLengthOf(group.random(ZR)), schemeIBMECH.getLengthOf(group.random(G1)), schemeIBMECH.getLengthOf(group.random(G2)), schemeIBMECH.getLengthOf(group.random(GT)), 		\
		schemeIBMECH.getLengthOf(mpk), schemeIBMECH.getLengthOf(msk), schemeIBMECH.getLengthOf(ek_sigma), schemeIBMECH.getLengthOf(dk_rho), schemeIBMECH.getLengthOf(ct)					\
	]
	del schemeIBMECH
	print("Original:", message)
	print("Decrypted:", m)
	print("Is the scheme correct (message == m)? {0}. ".format("Yes" if message == m else "No"))
	print("Time:", timeRecords)
	print("Memory:", memoryRecords)
	print("Size:", sizeRecords)
	print()
	return [group.groupType(), group.secparam, round if isinstance(round, int) else None, True, message == m] + timeRecords + memoryRecords + sizeRecords

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
	curveTypes = ("MNT159", "MNT201", "MNT224", "BN254", ("SS512", 512))
	roundCount, filePath = 20, "SchemeIBMECH.xlsx"
	columns = [																\
		"curveType", "secparam", "roundCount", "isSystemValid", "isSchemeCorrect", 		\
		"Setup (s)", "SKGen (s)", "RKGen (s)", "Enc (s)", "Dec (s)", 					\
		"Setup (B)", "SKGen (B)", "RKGen (B)", "Enc (B)", "Dec (B)", 					\
		"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 	\
		"mpk (B)", "msk (B)", "ek_sigma (B)", "dk_rho (B)", "CT (B)"					\
	]
	
	# Scheme #
	length, results = len(columns), []
	try:
		roundCount = max(1, roundCount)
		for curveType in curveTypes:
			average = Scheme(curveType, 0)
			for round in range(1, roundCount):
				result = Scheme(curveType, round)
				for idx in range(3, 5):
					average[idx] += result[idx]
				for idx in range(5, 10):
					average[idx] = -1 if average[idx] < 0 or result[idx] < 0 else average[idx] + result[idx]
				for idx in range(10, length):
					average[idx] = -1 if average[idx] <= 0 or result[idx] <= 0 else average[idx] + result[idx]
			average[2] = roundCount
			for idx in range(5, length):
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
	iRet = EXIT_SUCCESS if results and all([all([r == roundCount for r in result[3:5]] + [r > 0 for r in result[5:length]]) for result in results]) else EXIT_FAILURE
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