import os
from sys import argv, exit
from time import perf_counter, sleep
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element
	from charm.toolbox.matrixops import GaussEliminationinGroups
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


class Parser:
	def __init__(self:object, arguments:tuple|list) -> object:
		self.__arguments = tuple(argument for argument in arguments if isinstance(argument, str)) if isinstance(arguments, (tuple, list)) else ()
		self.__schemeName = "SchemeIBMECH" # os.path.splitext(os.path.basename(__file__))[0]
		self.__outputExtension = ".xlsx"
		self.__optionE = ("e", "/e", "-e", "encoding", "/encoding", "--encoding")
		self.__defaultE = "utf-8"
		self.__optionH = ("h", "/h", "-h", "help", "/help", "--help")
		self.__optionO = ("o", "/o", "-o", "output", "/output", "--output")
		self.__defaultO = "./{0}{1}".format(self.__schemeName, self.__outputExtension)
		self.__optionR = ("r", "/r", "-r", "round", "/round", "--round")
		self.__defaultR = 10
		self.__optionT = ("t", "/t", "-t", "time", "/time", "--time")
		self.__defaultT = float("inf")
		self.__optionY = ("y", "/y", "-y", "yes", "/yes", "--yes")
	def __escape(self:object, string) -> str:
		return string.replace("\\", "\\\\").replace("\"", "\\\"").replace("\a", "\\\a").replace("\b", "\\\b").replace("\n", "\\\n").replace("\r", "\\r").replace("\t", "\\\t").replace("\v", "\\\v")
	def __formatOption(self:object, option:tuple, pre:str = "[", sep:str = "|", suf:str = "]") -> str:
		if isinstance(option, tuple) and all(isinstance(op, str) for op in option):
			prefix = pre if isinstance(pre, str) else "["
			separator = sep if isinstance(sep, str) else "|"
			suffix = suf if isinstance(suf, str) else "]"
			return prefix + separator.join(option) + suffix
		else:
			return ""
	def __printHelp(self:object) -> None:
		print("This is a possible implementation of the IBMECH cryptography scheme in Python programming language based on the Python charm library. \n")
		print("Options (not case-sensitive): ")
		print("\t{0} [utf-8|utf-16|...]\t\tSpecify the encoding mode for CSV and TXT outputs. The default value is {1}. ".format(self.__formatOption(self.__optionE), self.__defaultE))
		print("\t{0}\t\tPrint this help document. ".format(self.__formatOption(self.__optionH)))
		print("\t{0} [.|./{1}.xlsx|./{1}.csv|...]\t\tSpecify the output file path, leaving it empty for console output. The default value is {2}. ".format(	\
			self.__formatOption(self.__optionO), self.__schemeName, self.__defaultO										\
		))
		print("\t{0} [1|2|5|10|20|50|100|...]\t\tSpecify the round count, which must be a positive integer. The default value is {1}. ".format(self.__formatOption(self.__optionR), self.__defaultR))
		print(																				\
			"\t{0} [0|0.1|1|10|...|inf]\t\tSpecify the waiting time before exiting, which should be non-negative. ".format(self.__formatOption(self.__optionT))	\
			+ "Passing nan, None, or inf requires users to manually press the enter key before exiting. The default value is {0}. ".format(self.__defaultT)		\
		)
		print("\t{0}\t\tIndicate to confirm the overwriting of the existing output file. \n".format(self.__formatOption(self.__optionY)))
	def __handlePath(self:object, path:str) -> str:
		if isinstance(path, str):
			return os.path.join(path, self.__schemeName + self.__outputExtension) if path.endswith("/") else path
		else:
			return self.__defaultO
	def parse(self:object) -> tuple:
		flag, encoding, outputFilePath, roundCount, waitingTime, overwritingConfirmed = max(EXIT_SUCCESS, EOF) + 1, self.__defaultE, self.__defaultO, self.__defaultR, self.__defaultT, False
		index, argumentCount, buffers = 1, len(self.__arguments), []
		while index < argumentCount:
			argument = self.__arguments[index].lower()
			if argument in self.__optionE:
				index += 1
				if index < argumentCount:
					try:
						__import__("codecs").lookup(self.__arguments[index])
						encoding = self.__arguments[index]
					except:
						flag = EOF
						buffers.append("Parser: The value [0] = \"{1}\" for the encoding option is invalid. ".format(index, self.__escape(self.__arguments[index])))
				else:
					flag = EOF
					buffers.append("Parser: The value for the encoding option is missing at [{0}]. ".format(index))
			elif argument in self.__optionH:
				self.__printHelp()
				flag = EXIT_SUCCESS
				break
			elif argument in self.__optionO:
				index += 1
				if index < argumentCount:
					outputFilePath = self.__handlePath(self.__arguments[index])
				else:
					flag = EOF
					buffers.append("Parser: The value for the output file path option is missing at [{0}]. ".format(index))
			elif argument in self.__optionR:
				index += 1
				if index < argumentCount:
					try:
						r = int(self.__arguments[index])
						if r >= 1:
							roundCount = r
						else:
							flag = EOF
							buffers.append("Parser: The value [{0}] = {1} for the round count option should be a positive integer. ".format(index, r))
					except:
						flag = EOF
						buffers.append("Parser: The type of the value [{0}] = \"{1}\" for the round count option is invalid. ".format(index, self.__escape(self.__arguments[index])))
				else:
					flag = EOF
					buffers.append("Parser: The value for the round count option is missing at [{0}]. ".format(index))
			elif argument in self.__optionT:
				index += 1
				if index < argumentCount:
					if self.__arguments[index].lower() in ("n", "nan", "none"):
						waitingTime = None
					else:
						try:
							t = float(self.__arguments[index])
							if t >= 0:
								waitingTime = int(t) if t.is_integer() else t
							else:
								flag = EOF
								buffers.append("Parser: The value [{0}] = {1} for the waiting time option should be a non-negative value. ".format(index, t))
						except:
							flag = EOF
							buffers.append("Parser: The type of the value [{0}] = \"{1}\" for the waiting time option is invalid. ".format(index, self.__escape(self.__arguments[index])))
				else:
					flag = EOF
					buffers.append("Parser: The value for the waiting time option is missing at [{0}]. ".format(index))
			elif argument in self.__optionY:
				overwritingConfirmed = True
			else:
				flag = EOF
				buffers.append("Parser: The option [{0}] = \"{1}\" is unknown. ".format(index, self.__escape(self.__arguments[index])))
			index += 1
		if EOF == flag:
			for buffer in buffers:
				print(buffer)
		return (flag, encoding, outputFilePath, roundCount, waitingTime, overwritingConfirmed)
	def checkOverwriting(self:object, outputFP:str, overwriting:bool) -> tuple:
		if isinstance(outputFP, str) and isinstance(overwriting, bool):
			outputFilePath, overwritingConfirmed = outputFP, overwriting
			while outputFilePath not in ("", ".") and os.path.isfile(outputFilePath):
				if not overwritingConfirmed:
					try:
						overwritingConfirmed = input("The file \"{0}\" exists. Overwrite the file or not [yN]? ".format(outputFilePath)).upper() in ("Y", "YES", "1", "T", "TRUE")
					except:
						print()
				if overwritingConfirmed:
					break
				else:
					try:
						outputFilePath = self.__handlePath(input("Please specify a new output file path or leave it empty for console output: "))
					except:
						print()
			return (outputFilePath, overwritingConfirmed)
		else:
			return (outputFP, overwriting)

class Saver:
	def __init__(self:object, outputFilePath:str = ".", columns:tuple|list|None = None, floatFormat:str = "%.9f", encoding:str = "utf-8") -> object:
		self.__outputFilePath = outputFilePath if isinstance(outputFilePath, str) else "."
		self.__columns = tuple(column for column in columns if isinstance(column, str)) if isinstance(columns, (tuple, list)) else None
		self.__floatFormat = floatFormat if isinstance(floatFormat, str) else "%.9f"
		self.__encoding = encoding if isinstance(encoding, str) else "utf-8"
	def __handleFolder(self:object, fd:str) -> bool:
		try:
			folder = str(fd)
		except:
			return False
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
	def initialize(self:object) -> bool:
		return self.__handleFolder(os.path.dirname(self.__outputFilePath))
	def save(self:object, results:tuple|list) -> bool:
		if isinstance(results, (tuple, list)) and results:
			if self.__outputFilePath in ("", "."):
				try:
					print("Saver: \n{0}\n".format(results))
					return True
				except BaseException as e:
					print("Saver: Results are not printable. Exceptions are as follows. \n\t{0}".format(e))
					return False
			else:
				while True:
					try:
						df = __import__("pandas").DataFrame(results, columns = self.__columns)
						if os.path.splitext(self.__outputFilePath)[1] == ".xlsx":
							df.to_excel(self.__outputFilePath, index = False, float_format = self.__floatFormat)
						else:
							df.to_csv(self.__outputFilePath, index = False, float_format = self.__floatFormat, encoding = self.__encoding)
						print("Saver: Successfully saved the results to \"{0}\" in the three-line table format. ".format(self.__outputFilePath))
						return True
					except KeyboardInterrupt:
						continue
					except BaseException:
						try:
							with open(self.__outputFilePath, "wt", encoding = self.__encoding) as f:
								for column in self.__columns[:-1]:
									f.write(column + "\t")
								for column in self.__columns[-1:]:
									f.write(column)
								for result in results:
									f.write("\n")
									for r in result[:-1]:
										f.write("{0}\t".format(r))
									for r in result[-1:]:
										f.write("{0}".format(r))
							print("Saver: Successfully saved the results to \"{0}\" in the plain text format. ".format(self.__outputFilePath))
							return True
						except KeyboardInterrupt:
							continue
						except BaseException as e:
							print("Saver: \n{0}\n\nFailed to save the results to \"{1}\" due to the following exception(s). \n\t{2}".format(results, self.__outputFilePath, e))
							return False
		else:
			print("Saver: The results are empty. ")
			return False

class SchemeIBMECH:
	def __init__(self:object, group:None|PairingGroup = None) -> object: # This scheme is applicable to symmetric and asymmetric groups of prime orders. 
		super().__init__()
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def __product(self:object, vec:tuple|list|set) -> Element:
		if isinstance(vec, (tuple, list, set)) and vec and all(isinstance(ele, Element) for ele in vec):
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
		g1 = self.__group.init(G1, 1) # $g_1 \gets 1_{\mathbb{G}_1}$
		g2 = self.__group.init(G2, 1) # $g_2 \gets 1_{\mathbb{G}_2}$
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		alpha, eta = self.__group.random(ZR), self.__group.random(ZR) # generate $\alpha, \eta \in \mathbb{Z}_r$ randomly
		zero, one = self.__group.init(ZR, 0), self.__group.random(ZR) # generate $\textbf{0}_{\mathbb{Z}_r}, \textbf{1}_{\mathbb{Z}_r} \in \mathbb{Z}_r$ randomly
		B = [[self.__group.random(ZR) for j in range(8)] for i in range(8)] # generate $\bm{B} \gets (\mathbb{Z}_r)^{8 \times 8}$ randomly
		D = tuple(tuple(g1 ** B[i][j] for j in range(8)) for i in range(4)) # $\mathbb{D}_{i, j} \gets g_1^{\bm{B}_{i, j}}, \forall i \in \{1, 2, 3, 4\}, \forall j \in \{1, 2, \cdots, 8\}$
		DStar = tuple(tuple(GaussEliminationinGroups([B[j] + [one if i == j else zero] for j in range(8)])) for i in range(4)) # $\mathbb{D}_i^* \gets \textit{GaussEliminationinGroups}(\bm{B} || [1 = i, 2 = i, \cdots, 8 = i]^\mathrm{T}), \forall i \in \{1, 2, 3, 4\}$
		del B
		gT = pair(g1, g2) # $g_T \gets e(g_1, g_2)$
		self.__mpk = (gT ** (alpha * one), gT ** (eta * one), D[0], D[1]) # $\textit{mpk} \gets (g_T^{\alpha \times \textbf{1}_{\mathbb{Z}_r}}, g_T^{\eta \times \textbf{1}_{\mathbb{Z}_r}}, D_1, D_2)$
		self.__msk = (alpha, eta, g1, g2, D[2], D[3], DStar[0], DStar[1], DStar[2], DStar[3]) # $\textit{msk} \gets (\alpha, \eta, g_1, g_2, \bm{d}_3, \bm{d}_4, \bm{d}_1^*, \bm{d}_2^*, \bm{d}_3^*, \bm{d}_4^*)$
		
		# Return #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def SKGen(self:object, sender:Element) -> tuple: # $\textbf{SKGen}(\sigma) \rightarrow \textit{ek}_\sigma$
		# Check #
		if not self.__flag:
			print("SKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``SKGen`` subsequently. ")
			self.Setup()
		if isinstance(sender, Element) and sender.type == ZR: # type check
			sigma = sender
		else:
			sigma = self.__group.random(ZR)
			print("SKGen: The variable $\\sigma$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		eta, d3, d4 = self.__msk[1], self.__msk[4], self.__msk[5]
		
		# Scheme #
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_r$
		ek_sigma = tuple(d3[i] ** (eta + r * sigma) / d4[i] ** r for i in range(8)) # $\textit{ek}_\sigma \gets \frac{\bm{d}_{3, i}^{\eta + r \sigma}}{\bm{d}_{4, i}^r}, \forall i \in \{1, 2, \cdots, 8\}$
		
		# Return #
		return ek_sigma # \textbf{return} $\textit{ek}_\sigma$
	def RKGen(self:object, receiver:Element) -> tuple: # $\textbf{RKGen}(\rho) \rightarrow \textit{dk}_\rho$
		# Check #
		if not self.__flag:
			print("RKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``RKGen`` subsequently. ")
			self.Setup()
		if isinstance(receiver, Element) and receiver.type == ZR: # type check
			rho = receiver
		else:
			rho = self.__group.random(ZR)
			print("RKGen: The variable $\\rho$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		gTToThePowerOfEta = self.__mpk[1]
		alpha, g2, DStar1, DStar2, DStar3, DStar4 = self.__msk[0], self.__msk[3], self.__msk[6], self.__msk[7], self.__msk[8], self.__msk[9]
		
		# Scheme #
		s, s1, s2 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $s, s_1, s_2 \in \mathbb{Z}_r$ randomly
		k1 = tuple(g2 ** (DStar1[i] * (alpha + s1 * rho) - s1 * DStar2[i] + s * DStar3[i]) for i in range(8)) # $k_1 \gets \{g_2^{\bm{d}_{1, i} \cdot (\alpha + s_1 \rho) - s_1 \bm{d}_{2, i} + s \bm{d}_{3, i}}, \forall i \in \{1, 2, \cdots, 8\}\}$
		k2 = tuple(g2 ** (s2 * (rho * DStar1[i] - DStar2[i]) + s * DStar4[i]) for i in range(8)) # $k_2 \gets \{g_2^{s_2 \cdot (\rho * \bm{d}_{1, i} - \bm{d}_{2, i}) + s \bm{d}_{4, i}}, \forall i \in \{1, 2, \cdots, 8\}\}$
		k3 = gTToThePowerOfEta ** s # $k_3 \gets (g_T^\eta)^s$
		dk_rho = (k1, k2, k3) # $\textit{dk}_\rho \gets (k_1, k_2, k_3)$
		
		# Return #
		return dk_rho # \textbf{return} $\textit{dk}_\rho$
	def Enc(self:object, eksigma:tuple, receiver:Element, message:Element) -> tuple: # $\textbf{Enc}(\textit{ek}_\sigma, \textit{rcv}, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(eksigma, tuple) and len(eksigma) == 8 and all(isinstance(ele, Element) for ele in eksigma): # hybrid check
			ek_sigma = eksigma
		else:
			ek_sigma = self.SKGen(self.__group.random(ZR))
			print("Enc: The variable $\\textit{ek}_\\sigma$ should be a tuple containing 8 elements but it is not, which has been generated randomly. ")
		if isinstance(receiver, Element) and receiver.type == ZR: # type check
			rcv = receiver
		else:
			rcv = self.__group.random(ZR)
			print("Enc: The variable $\\textit{rcv}$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			m = message
		else:
			m = self.__group.random(GT)
			print("Enc: The variable $m$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		gTToThePowerOfAlpha, D1, D2 = self.__mpk[0], self.__mpk[2], self.__mpk[3]
		
		# Scheme #
		z = self.__group.random(ZR) # generate $z \gets \mathbb{Z}_r$ randomly
		C = tuple(D1[i] ** z * D2[i] ** (z * rcv) * ek_sigma[i] for i in range(8)) # $C \gets \{\bm{d}_{1, i}^z \bm{d}_{2, i}^{z \cdot \textit{rcv}} \cdot (\textit{ek}_\sigma)_i, \forall i \in \{1, 2, \cdots, 8\}\}$
		C0 = gTToThePowerOfAlpha ** z * m # $C_0 \gets (g_T^\alpha)^z m$
		ct = (C, C0) # $\textit{ct} \gets (C, C_0)$
		
		# Return #
		return ct # \textbf{return} $\textit{ct}$
	def Dec(self:object, dkrho:tuple, sender:Element, cipherText:tuple) -> Element: # $\textbf{Dec}(\textit{dk}_\rho, \textit{snd}, \textit{ct}) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if (																																\
			isinstance(dkrho, tuple) and len(dkrho) == 3 and isinstance(dkrho[0], tuple) and len(dkrho[0]) == 8 and all(isinstance(ele, Element) for ele in dkrho[0])		\
			and isinstance(dkrho[1], tuple) and len(dkrho[1]) == 8 and all(isinstance(ele, Element) for ele in dkrho[1]) and isinstance(dkrho[2], Element)				\
		): # hybrid check
			dk_rho = dkrho
		else:
			dk_rho = self.RKGen(self.__group.random(ZR))
			print("Dec: The variable $\\textit{dk}_\\rho$ should be a tuple containing 2 tuples and an element but it is not, which has been generated randomly. ")
		if isinstance(sender, Element) and sender.type == ZR: # type check
			snd = sender
		else:
			snd = self.__group.random(ZR)
			print("Dec: The variable $\\textit{snd}$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 2 and isinstance(cipherText[0], tuple) and len(cipherText[0]) == 8 and all(isinstance(ele, Element) for ele in cipherText[0]) and isinstance(cipherText[1], Element): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.SKGen(self.__group.random(ZR)), self.__group.random(ZR), self.__group.random(GT))
			print("Dec: The variable $\textit{ct}$ should be a tuple containing a tuple and an element but it is not, which has been generated randomly. ")
		
		# Unpack #
		k1, k2, k3 = dk_rho
		C, C0 = ct
				
		# Scheme #
		m = C0 * k3 / self.__product(tuple(pair(C[i], k1[i] * k2[i] ** snd) for i in range(8))) # $m \gets \frac{C_0 k_3}{\prod\limits_{i = 1}^8 e(C_i, k_{1, i} k_{2, i}^\textit{snd})}$
		
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
		elif isinstance(obj, int) or callable(obj):
			return (self.__group.secparam + 7) >> 3
		else:
			return -1


def conductScheme(curveType:tuple|list|str, run:int|None = None) -> list:
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
		else:
			print("curveType = Unknown")
		if isinstance(run, int) and run >= 1:
			print("run =", run)
		print("Is the system valid? No. \n\t{0}".format(e))
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [run if isinstance(run, int) else None] + [False] * 2 + [-1] * 14																																	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(run, int) and run >= 1:
		print("run =", run)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBMECH = SchemeIBMECH(group)
	timeRecords = []

	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBMECH.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# SKGen #
	startTime = perf_counter()
	sigma = group.random(ZR)
	ek_sigma = schemeIBMECH.SKGen(sigma)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# RKGen #
	startTime = perf_counter()
	rho = group.random(ZR)
	dk_rho = schemeIBMECH.RKGen(rho)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = group.random(GT)
	ct = schemeIBMECH.Enc(ek_sigma, rho, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec #
	startTime = perf_counter()
	m = schemeIBMECH.Dec(dk_rho, sigma, ct)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, message == m]
	spaceRecords = [																																									\
		schemeIBMECH.getLengthOf(group.random(ZR)), schemeIBMECH.getLengthOf(group.random(G1)), schemeIBMECH.getLengthOf(group.random(G2)), schemeIBMECH.getLengthOf(group.random(GT)), 		\
		schemeIBMECH.getLengthOf(mpk), schemeIBMECH.getLengthOf(msk), schemeIBMECH.getLengthOf(ek_sigma), schemeIBMECH.getLengthOf(dk_rho), schemeIBMECH.getLengthOf(ct)					\
	]
	del schemeIBMECH
	print("Original:", message)
	print("Decrypted:", m)
	print("Is the scheme correct (message == m)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, run if isinstance(run, int) else None] + booleans + timeRecords + spaceRecords


def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, roundCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
		outputFilePath, overwritingConfirmed = parser.checkOverwriting(outputFilePath, overwritingConfirmed)
		del parser
		
		# Parameters #
		curveTypes = ("MNT159", "MNT201", "MNT224", "BN254", ("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
		queries = ("curveType", "secparam", "roundCount")
		validators = ("isSystemValid", "isSchemeCorrect")
		metrics = (																			\
			"Setup (s)", "SKGen (s)", "RKGen (s)", "Enc (s)", "Dec (s)", 					\
			"elementOfZR (B)", "elementOfG1 (B)", "elementOfG2 (B)", "elementOfGT (B)", 	\
			"mpk (B)", "msk (B)", "ek_sigma (B)", "dk_rho (B)", "CT (B)"					\
		)
		
		# Scheme #
		columns, qLength, results = queries + validators + metrics, len(queries), []
		length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
		saver = Saver(outputFilePath, columns)
		if saver.initialize():
			try:
				for curveType in curveTypes:
					averages = conductScheme(curveType, run = 0)
					for run in range(2, roundCount + 1):
						result = conductScheme(curveType, run = run)
						for idx in range(qLength, qvLength):
							averages[idx] += result[idx]
						for idx in range(qvLength, length):
							averages[idx] = -1 if averages[idx] < 0 or result[idx] < 0 else averages[idx] + result[idx]
					averages[avgIndex] = roundCount
					for idx in range(qvLength, length):
						averages[idx] = -1 if averages[idx] <= 0 else averages[idx] / roundCount
						averages[idx] = int(averages[idx]) if averages[idx].is_integer() else averages[idx]
					results.append(averages)
					saver.save(results)
			except KeyboardInterrupt:
				print("\nThe experiments were interrupted by users. Saved results are retained. ")
			except BaseException as e:
				print("The experiments were interrupted by the following exceptions. Saved results are retained. \n\t{0}".format(e))
			errorLevel = EXIT_SUCCESS if results and all(all(tuple(r == roundCount for r in result[qLength:qvLength]) + tuple(r > 0 for r in result[qvLength:length])) for result in results) else EXIT_FAILURE
		else:
			print("Failed to initialize the directory for the output file path \"{0}\". ".format(outputFilePath))
			errorLevel = EOF
	elif EXIT_SUCCESS == flag:
		errorLevel = flag
	else:
		errorLevel = EOF
	try:
		if 0 == waitingTime:
			print("The execution of the Python script has finished ({0}). ".format(errorLevel))
		elif isinstance(waitingTime, (float, int)) and 0 < waitingTime < float("inf"):
			print("Please wait for the countdown ({0} second(s)) to end, or exit the program manually like pressing the \"Ctrl + C\" ({1}). ".format(waitingTime, errorLevel))
			sleep(waitingTime)
		else:
			print("Please press the enter key to exit ({0}). ".format(errorLevel))
			input()
	except:
		print()
	print()
	return errorLevel



if "__main__" == __name__:
	exit(main())