import os
from sys import argv, exit
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
		self.__schemeName = "SchemeARES" # os.path.splitext(os.path.basename(__file__))[0]
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
		print("This is a possible implementation of the ARES cryptography scheme in Python programming language based on the Python charm library. \n")
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

class SchemeARES:
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
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def Setup(self:object) -> tuple: # $\textbf{Setup}() \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		g0, g1 = self.__group.random(G1), self.__group.random(G1) # generate $g_0, g_1 \in \mathbb{G}_1$ randomly
		w, t1, t2, t3, t4 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $w, t_1, t_2, t_3, t_4 \in \mathbb{Z}_r$
		Omega = pair(g, g) ** (t1 * t2 * w) # $\Omega \gets e(g, g)^{t_1 t_2 w}$
		v1 = g ** t1 # $v \gets g^{t_1}$
		v2 = g ** t2 # $v \gets g^{t_2}$
		v3 = g ** t3 # $v \gets g^{t_3}$
		v4 = g ** t4 # $v \gets g^{t_4}$
		self.__mpk = (Omega, g, g0, g1, v1, v2, v3, v4) # $\textit{mpk} \gets (Omega, g, g_0, g_1, v_1, v_2, v_3, v_4)$
		self.__msk = (w, t1, t2, t3, t4) # $\textit{msk} \gets (w, t_1, t_2, t_3, t_4)$
		
		# Return #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def Extract(self:object, identity:Element) -> tuple: # $\textbf{Extract}(\textit{Id}) \rightarrow \textit{Pvk}_\textit{Id}$
		# Check #
		if not self.__flag:
			self.Setup()
			print("Extract: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Extract`` subsequently. ")
		if isinstance(identity, Element) and identity.type == ZR: # type check
			Id = identity
		else:
			Id = self.__group.random(ZR)
			print("Extract: The variable $\\textit{Id}$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1 = self.__mpk[1], self.__mpk[2], self.__mpk[3]
		w, t1, t2, t3, t4 = self.__msk
		
		# Scheme #
		r1, r2 = self.__group.random(ZR), self.__group.random(ZR) # generate $r1, r2 \in \mathbb{Z}_r$ randomly
		d0 = g ** (r1 * t1 * t2 + r2 * t3 * t4) # $d_0 \gets g^{r_1 t_1 t_2 + r_2 t_3 t_4}$
		d1 = g ** (-(w * t2)) * (g0 * g1 ** Id) ** (-(r1 * t2)) # $d_1 \gets g^{- w t_2} \cdot (g_0 g_1^\textit{Id})^{-  r_1 t_2}$
		d2 = g ** (-(w * t1)) * (g0 * g1 ** Id) ** (-(r1 * t1)) # $d_2 \gets g^{- w t_1} \cdot (g_0 g_1^\textit{Id})^{-  r_1 t_1}$
		d3 = (g0 * g1 ** Id) ** (-(r2 * t4)) # $d_3 \gets (g_0 g_1^\textit{Id})^{-  r_2 t_4}$
		d4 = (g0 * g1 ** Id) ** (-(r2 * t3)) # $d_4 \gets (g_0 g_1^\textit{Id})^{-  r_2 t_3}$
		Pvk_Id = (d0, d1, d2, d3, d4) # $\textit{Pvk}_\textit{Id} \gets (d_0, d_1, d_2, d_3, d_4)$
		
		# Return #
		return Pvk_Id # \textbf{return} $\textit{Pvk}_\textit{Id}$
	def TSK(self:object, identity:Element) -> tuple: # $\textbf{TSK}(\textit{Id}) \rightarrow \textit{Pvk}_\textit{Id}$
		# Check #
		if not self.__flag:
			print("TSK: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``TSK`` subsequently. ")
			self.Setup()
		if isinstance(identity, Element) and identity.type == ZR: # type check
			Id = identity
		else:
			Id = self.__group.random(ZR)
			print("TSK: The variable $\\textit{Id}$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1 = self.__mpk[1], self.__mpk[2], self.__mpk[3]
		w, t1, t2, t3, t4 = self.__msk
		
		# Scheme #
		r1, r2 = self.__group.random(ZR), self.__group.random(ZR) # generate $r1, r2 \in \mathbb{Z}_r$ randomly
		d0 = g ** (r1 * t1 * t2 + r2 * t3 * t4) # $d_0 \gets g^{r_1 t_1 t_2 + r_2 t_3 t_4}$
		d1 = (g0 * g1 ** Id) ** (-(r1 * t2)) # $d_1 \gets (g_0 g_1^\textit{Id})^{-  r_1 t_2}$
		d2 = (g0 * g1 ** Id) ** (-(r1 * t1)) # $d_2 \gets (g_0 g_1^\textit{Id})^{-  r_1 t_1}$
		d3 = (g0 * g1 ** Id) ** (-(r2 * t4)) # $d_3 \gets (g_0 g_1^\textit{Id})^{-  r_2 t_4}$
		d4 = (g0 * g1 ** Id) ** (-(r2 * t3)) # $d_4 \gets (g_0 g_1^\textit{Id})^{-  r_2 t_3}$
		Pvk_Id = (d0, d1, d2, d3, d4) # $\textit{Pvk}_\textit{Id} \gets (d_0, d_1, d_2, d_3, d_4)$
		
		# Return #
		return Pvk_Id # \textbf{return} $\textit{Pvk}_\textit{Id}$
	def Encrypt(self:object, identity:Element, message:Element) -> tuple: # $\textbf{Encrypt}(\textit{Id}, m) \rightarrow \textit{CT}$
		# Check #
		if not self.__flag:
			print("Encrypt: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Encrypt`` subsequently. ")
			self.Setup()
		if isinstance(identity, Element) and identity.type == ZR: # type check
			Id = identity
		else:
			Id = self.__group.random(ZR)
			print("Encrypt: The variable $\\textit{Id}$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			M = message
		else:
			M = self.__group.random(GT)
			print("Encrypt: The variable $M$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		Omega, g0, g1, v1, v2, v3, v4 = self.__mpk[0], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7]
		
		# Scheme #
		s, s1, s2 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $s, s_1, s_2 \in \mathbb{Z}_r$ randomly
		CPi = Omega ** s * M # $C' \gets \Omega^s M$
		C0 = (g0 * g1 ** Id) ** s # $(g_0 g_1^\textit{Id})^s$
		C1 = v1 ** (s - s1) # $C_1 \gets v_1^{s - s_1}$
		C2 = v2 ** s1 # $C_2 \gets v_2^{s_1}$
		C3 = v3 ** (s - s2) # $C_3 \gets v_3^{s - s_2}$
		C4 = v4 ** s2 # $C_4 \gets v_4^{s_2}$
		CT = (CPi, C0, C1, C2, C3, C4) # $\textit{CT} \gets (C', C_0, C_1, C_2, C_3, C_4)$
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Decrypt(self:object, PvkId:tuple, cipherText:tuple) -> Element: # $\textbf{Decrypt}(\textit{Pvk}_\textit{id}, \textit{CT}) \rightarrow M$
		# Check #
		if not self.__flag:
			print("Decrypt: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Decrypt`` subsequently. ")
			self.Setup()
		if isinstance(PvkId, tuple) and len(PvkId) == 5 and all(isinstance(ele, Element) for ele in PvkId): # hybrid check
			Pvk_Id = PvkId
		else:
			Pvk_Id = self.Extract(self.__group.random(ZR))
			print("Decrypt: The variable $\\textit{Pvk}_\\textit{Id}$ should be a tuple containing 5 elements but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 6 and all(isinstance(ele, Element) for ele in cipherText): # hybrid check
			CT = cipherText
		else:
			CT = self.Encrypt(self.__group.random(ZR), self.__group.random(ZR))
			print("Decrypt: The variable $\\textit{CT}$ should be a tuple containing 6 elements but it is not, which has been generated randomly. ")
		
		# Unpack #
		d0, d1, d2, d3, d4 = Pvk_Id
		CPi, C0, C1, C2, C3, C4 = CT
		
		# Scheme #
		M = CPi * pair(C0, d0) * pair(C1, d1) * pair(C2, d2) * pair(C3, d3) * pair(C4, d4) # $M \gets C' \cdot e(C_0, d_0) \cdot e(C_1, d_1) \cdot e(C_2, d_2) \cdot e(C_3, d_3) \cdot e(C_4, d_4)$
		
		# Return #
		return M # \textbf{return} $M$
	def TVerify(self:object, PvkId:tuple, cipherText:tuple) -> bool: # $\textbf{TVerify}(\textit{Pvk}_\textit{id}, \textit{CT}) \rightarrow y, y \in \{0, 1\}$
		# Check #
		if not self.__flag:
			print("TVerify: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``TVerify`` subsequently. ")
			self.Setup()
		if isinstance(PvkId, tuple) and len(PvkId) == 5 and all(isinstance(ele, Element) for ele in PvkId): # hybrid check
			Pvk_Id = PvkId
		else:
			Pvk_Id = self.Extract(self.__group.random(ZR))
			print("TVerify: The variable $\\textit{Pvk}_\\textit{Id}$ should be a tuple containing 5 elements but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 6 and all(isinstance(ele, Element) for ele in cipherText): # hybrid check
			CT = cipherText
		else:
			CT = self.Encrypt(self.__group.random(ZR), self.__group.random(ZR))
			print("TVerify: The variable $\\textit{CT}$ should be a tuple containing 6 elements but it is not, which has been generated randomly. ")
		
		# Unpack #
		d0, d1, d2, d3, d4 = Pvk_Id
		CPi, C0, C1, C2, C3, C4 = CT
		
		# Scheme #
		pass
		
		# Return #
		return pair(C0, d0) * pair(C1, d1) * pair(C2, d2) * pair(C3, d3) * pair(C4, d4) == self.__group.init(GT) # \textbf{return} $e(C_0, d_0) \cdot e(C_1, d_1) \cdot e(C_2, d_2) \cdot e(C_3, d_3) \cdot e(C_4, d_4) = 1 (\mathbb{G}_T)$
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


def conductScheme(curveType:tuple|list|str, round:int|None = None) -> list:
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
		if isinstance(round, int) and round >= 0:
			print("round =", round)
		print("Is the system valid? No. \n\t{0}".format(e))
		return (																																														\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])		\
			+ [round if isinstance(round, int) and round >= 0 else None] + [False] * 3 + [-1] * 14																														\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeARES = SchemeARES(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeARES.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Extract #
	startTime = perf_counter()
	Id = group.random(ZR)
	Pvk_Id = schemeARES.Extract(Id)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# TSK #
	startTime = perf_counter()
	Pvk_IdTraced = schemeARES.TSK(Id)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Encrypt #
	startTime = perf_counter()
	message = group.random(GT)
	CT = schemeARES.Encrypt(Id, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Decrypt #
	startTime = perf_counter()
	M = schemeARES.Decrypt(Pvk_Id, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# TVerify #
	startTime = perf_counter()
	bRet = schemeARES.TVerify(Pvk_IdTraced, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, message == M, bRet]
	spaceRecords = [																																			\
		schemeARES.getLengthOf(group.random(ZR)), schemeARES.getLengthOf(group.random(G1)), schemeARES.getLengthOf(group.random(GT)), 								\
		schemeARES.getLengthOf(mpk), schemeARES.getLengthOf(msk), schemeARES.getLengthOf(Pvk_Id), schemeARES.getLengthOf(Pvk_IdTraced), schemeARES.getLengthOf(CT)	\
	]
	del schemeARES
	print("Original:", message)
	print("Decrypted:", M)
	print("Is the scheme correct (message == M)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Is the tracing verified? {0}. ".format("Yes" if booleans[2] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, round if isinstance(round, int) else None] + booleans + timeRecords + spaceRecords


def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, roundCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
		outputFilePath, overwritingConfirmed = parser.checkOverwriting(outputFilePath, overwritingConfirmed)
		del parser
		
		# Parameters #
		curveTypes = (("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
		queries = ("curveType", "secparam", "roundCount")
		validators = ("isSystemValid", "isSchemeCorrect", "isTracingVerified")
		metrics = (																					\
			"Setup (s)", "Extract (s)", "TSK (s)", "Encrypt (s)", "Decrypt (s)", "TVerify (s)", 	\
			"elementOfZR (B)", "elementOfG1 (B)", "elementOfGT (B)", 								\
			"mpk (B)", "msk (B)", "Pvk_Id (B)", "Pvk_IdTraced (B)", "CT (B)"						\
		)
		
		# Scheme #
		columns, qLength, results = queries + validators + metrics, len(queries), []
		length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
		saver = Saver(outputFilePath, columns)
		if saver.initialize():
		try:
			for curveType in curveTypes:
				averages = conductScheme(curveType, round = 0)
				for round in range(1, roundCount):
					result = conductScheme(curveType, round = round)
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