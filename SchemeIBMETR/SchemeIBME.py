import os
from sys import argv, exit
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


class Parser:
	def __init__(self:object, arguments:tuple|list) -> object:
		self.__arguments = tuple(argument for argument in arguments if isinstance(argument, str)) if isinstance(arguments, (tuple, list)) else ()
		self.__schemeName = "SchemeIBME" # os.path.splitext(os.path.basename(__file__))[0]
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
		print("This is a possible implementation of the IBME cryptography scheme in Python programming language based on the Python charm library. \n")
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

class SchemeIBME:
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
		r, s = self.__group.random(ZR), self.__group.random(ZR) # generate $r, s \in \mathbb{Z}_r$ randomly
		P = self.__group.init(G1, 1) # $P \gets 1{\mathbb{G}_1}$
		P0 = r * P # $P_0 \gets r \cdot P$
		H = lambda x:self.__group.hash(x, G1) # $H_1: \mathbb{Z}_r \rightarrow \mathbb{G}_1$
		mask = bytes([randbelow(256) for _ in range(len(self.__group.serialize(self.__group.random(ZR))))]) # generate $\textit{mask}, \|\textit{mask}\| \gets \|e\|, e \in \mathbb{Z}_r$ randomly
		HPrime = lambda x:self.__group.hash(bytes([a ^ b for a, b in zip(self.__group.serialize(x), mask)]), G1) # $H': \mathbb{Z}_r \oplus \textit{mask} \rightarrow \mathbb{G}_1$
		self.__mpk = (P, P0, H, HPrime) # $\textit{mpk} \gets (P, P_0, H, H')$
		self.__msk = (r, s) # $\textit{msk} \gets (r, s)$
		
		# Return #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def SKGen(self:object, sender:Element) -> Element: # $\textbf{SKGen}(S) \rightarrow \textit{ek}_S$
		# Check #
		if not self.__flag:
			self.Setup()
			print("SKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``SKGen`` subsequently. ")
		if isinstance(sender, Element) and sender.type == ZR: # type check
			S = sender
		else:
			S = self.__group.random(ZR)
			print("SKGen: The variable $S$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		HPrime = self.__mpk[-1]
		s = self.__msk[1]
		
		# Scheme #
		ek_S = s * HPrime(S) # $\textit{ek}_S \gets s \cdot H'(S)$
		
		# Return #
		return ek_S # \textbf{return} $\textit{ek}_S$
	def RKGen(self:object, receiver:Element) -> Element: # $\textbf{RKGen}(S) \rightarrow \textit{dk}_R$
		# Check #
		if not self.__flag:
			self.Setup()
			print("RKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``RKGen`` subsequently. ")
		if isinstance(receiver, Element) and receiver.type == ZR: # type check
			R = receiver
		else:
			R = self.__group.random(ZR)
			print("RKGen: The variable $R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		H = self.__mpk[-2]
		r, s = self.__msk
		
		# Scheme #
		H_R = H(R) # $H_R \gets H(R)$
		dk1 = r * H_R # $\textit{dk}_1 \gets r \cdot H_R$
		dk2 = s * H_R # $\textit{dk}_2 \gets s \cdot H_R$
		dk3 = H_R # $\textit{dk}_3 \gets H_R$
		dk_R = (dk1, dk2, dk3) # $\textit{dk}_R \gets (\textit{dk}_1, \textit{dk}_2, \textit{dk}_3)$
		
		# Return #
		return dk_R # \textbf{return} $\textit{dk}_R$
	def Enc(self:object, ekS:Element, receiver:Element, message:int|bytes) -> tuple: # $\textbf{Enc}(\textit{ek}_S, R, M) \rightarrow C$
		# Check #
		if not self.__flag:
			self.Setup()
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
		if isinstance(ekS, Element):
			ek_S = ekS
		else:
			ek_S = self.SKGen(self.__group.random(ZR))
			print("Enc: The variable $\\textit{ek}_S$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(receiver, Element) and receiver.type == ZR: # type check
			R = receiver
		else:
			R = self.__group.random(ZR)
			print("Enc: The variable $R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(message, int) and message >= 0: # type check
			M = message & self.__operand
			if message != M:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			M = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			M = int.from_bytes(b"SchemeIBME", byteorder = "big") & self.__operand
			print("Enc: The variable $M$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemeIBME\". ")
		
		# Unpack #
		H = self.__mpk[-2]
		P, P0 = self.__mpk[0], self.__mpk[1]
		
		# Scheme #
		u, t = self.__group.random(ZR), self.__group.random(ZR) # generate $u, t \in \mathbb{Z}_r$ randomly
		T = t * P # $T \gets t \cdot P$
		U = u * P # $U \gets u \cdot P$
		H_R = H(R) # $H_R \gets H(R)$
		k_R = pair(H_R, u * P0) # $k_R \gets e(H_R, u \cdot P_0)$
		k_S = pair(H_R, T + ek_S) # $k_S \gets e(H_R, T + \textit{ek}_S)$
		V = M ^ int.from_bytes(self.__group.serialize(k_R), byteorder = "big") ^ int.from_bytes(self.__group.serialize(k_S), byteorder = "big") # $V \gets M \oplus k_R \oplus k_S$
		C = (T, U, V) # $C \gets (T, U, V)$
		
		# Return #
		return C # \textbf{return} $C$	
	def Dec(self:object, dkR:tuple, sender:Element, cipher:tuple) -> int: # $\textbf{Dec}(\textit{dk}_R, S, C) \rightarrow M$
		# Check #
		if not self.__flag:
			self.Setup()
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
		if isinstance(dkR, tuple) and len(dkR) == 3 and all(isinstance(ele, Element) for ele in dkR): # hybrid check
			dk_R = dkR
		else:
			dk_R = self.RKGen(self.__group.random(ZR))
			print("Dec: The variable $\\textit{dk}_R$ should be a tuple containing 3 elements but it is not, which has been generated randomly. ")
		if isinstance(sender, Element) and sender.type == ZR: # type check
			S = sender
		else:
			S = self.__group.random(ZR)
			print("Dec: The variable $S$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 3 and isinstance(cipher[0], Element) and isinstance(cipher[1], Element) and isinstance(cipher[2], int): # hybrid check
			C = cipher
		else:
			C = self.Enc(self.SKGen(self.__group.random(ZR)), self.__group.random(ZR), b"SchemeIBME")
			print("Dec: The variable $C$ should be a tuple containing 2 elements and an ``int`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		HPrime = self.__mpk[-1]
		dk1, dk2, dk3 = dk_R
		T, U, V = C
		
		# Scheme #
		k_R = pair(dk1, U) # $k_R \gets e(\textit{dk}_1, U)$
		HPrime_S = HPrime(S) # $H'_S \gets H'(S)$
		k_S = pair(dk3, T) * pair(HPrime_S, dk2) # $k_S \gets e(\textit{dk}_3, T)$
		M = V ^ int.from_bytes(self.__group.serialize(k_R), byteorder = "big") ^ int.from_bytes(self.__group.serialize(k_S), byteorder = "big") # $M \gets V \oplus k_R \oplus k_S$
		
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
		if isinstance(run, int) and run >= 1:
			print("run =", run)
		print("Is the system valid? No. \n\t{0}".format(e))
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [run if isinstance(run, int) else None] + [False] * 2 + [-1] * 13																																	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(run, int) and run >= 1:
		print("run =", run)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBME = SchemeIBME(group)
	timeRecords = []

	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBME.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# SKGen #
	startTime = perf_counter()
	S = group.random(ZR)
	ek_S = schemeIBME.SKGen(S)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# RKGen #
	startTime = perf_counter()
	R = group.random(ZR)
	dk_R = schemeIBME.RKGen(R)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = int.from_bytes(b"SchemeIBME", byteorder = "big")
	C = schemeIBME.Enc(ek_S, R, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec #
	startTime = perf_counter()
	M = schemeIBME.Dec(dk_R, S, C)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, message == M]
	spaceRecords = [																																	\
		schemeIBME.getLengthOf(group.random(ZR)), schemeIBME.getLengthOf(group.random(G1)), schemeIBME.getLengthOf(group.random(GT)), 						\
		schemeIBME.getLengthOf(mpk), schemeIBME.getLengthOf(msk), schemeIBME.getLengthOf(ek_S), schemeIBME.getLengthOf(dk_R), schemeIBME.getLengthOf(C)		\
	]
	del schemeIBME
	print("Original:", message)
	print("Decrypted:", M)
	print("Is the scheme correct (message == M)? {0}. ".format("Yes" if booleans[1] else "No"))
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
		curveTypes = (("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
		queries = ("curveType", "secparam", "roundCount")
		validators = ("isSystemValid", "isSchemeCorrect")
		metrics = (															\
			"Setup (s)", "SKGen (s)", "RKGen (s)", "Enc (s)", "Dec (s)", 	\
			"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)",		\
			"mpk (B)", "msk (B)", "ek_S (B)", "dk_R (B)", "C (B)"			\
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