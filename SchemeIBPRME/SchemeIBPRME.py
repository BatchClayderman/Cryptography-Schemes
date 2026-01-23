import os
from sys import argv, exit
from math import ceil, log
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
		self.__schemeName = "SchemeIBPRME" # os.path.splitext(os.path.basename(__file__))[0]
		self.__outputExtension = ".xlsx"
		self.__optionE = ("e", "/e", "-e", "encoding", "/encoding", "--encoding")
		self.__defaultE = "utf-8"
		self.__optionH = ("h", "/h", "-h", "help", "/help", "--help")
		self.__optionO = ("o", "/o", "-o", "output", "/output", "--output")
		self.__defaultO = "./{0}{1}".format(self.__schemeName, self.__outputExtension)
		self.__optionR = ("r", "/r", "-r", "round", "/round", "--round")
		self.__defaultR = 100
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
		print("This is the official implementation of the IBPRME cryptography scheme in Python programming language based on the Python charm library. \n")
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
	def handlePath(self:object, path:str) -> str:
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
						buffers.append("CL: The value [0] = \"{1}\" for the encoding option is invalid. ".format(index, self.__escape(self.__arguments[index])))
				else:
					flag = EOF
					buffers.append("CL: The value for the encoding option is missing at [{0}]. ".format(index))
			elif argument in self.__optionH:
				self.__printHelp()
				flag = EXIT_SUCCESS
				break
			elif argument in self.__optionO:
				index += 1
				if index < argumentCount:
					outputFilePath = self.handlePath(self.__arguments[index])
				else:
					flag = EOF
					buffers.append("CL: The value for the output file path option is missing at [{0}]. ".format(index))
			elif argument in self.__optionR:
				index += 1
				if index < argumentCount:
					try:
						r = int(self.__arguments[index])
						if r >= 1:
							roundCount = r
						else:
							flag = EOF
							buffers.append("CL: The value [{0}] = {1} for the round count option should be a positive integer. ".format(index, r))
					except:
						flag = EOF
						buffers.append("CL: The type of the value [{0}] = \"{1}\" for the round count option is invalid. ".format(index, self.__escape(self.__arguments[index])))
				else:
					flag = EOF
					buffers.append("CL: The value for the round count option is missing at [{0}]. ".format(index))
			elif argument in self.__optionT:
				index += 1
				if index < argumentCount:
					if self.__arguments[index].lower() in ("n", "nan", "none"):
						waitingTime = None
					else:
						try:
							t = float(self.__arguments[index])
							if t >= 0:
								waitingTime = t
							else:
								flag = EOF
								buffers.append("CL: The value [{0}] = {1} for the waiting time option should be a non-negative value. ".format(index, t))
						except:
							flag = EOF
							buffers.append("CL: The type of the value [{0}] = \"{1}\" for the waiting time option is invalid. ".format(index, self.__escape(self.__arguments[index])))
				else:
					flag = EOF
					buffers.append("CL: The value for the waiting time option is missing at [{0}]. ".format(index))
			elif argument in self.__optionY:
				overwritingConfirmed = True
			else:
				flag = EOF
				buffers.append("CL: The option [{0}] = \"{1}\" is unknown. ".format(index, self.__escape(self.__arguments[index])))
			index += 1
		if EOF == flag:
			for buffer in buffers:
				print(buffer)
		return (flag, encoding, outputFilePath, roundCount, waitingTime, overwritingConfirmed)

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
							df.to_csv(self.__outputFilePath, index = False, float_format = self.__floatFormat, encoding = encoding)
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

class SchemeIBPRME:
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
		q = self.__group.order() # $q \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		h = self.__group.random(G1) # generate $h \in \mathbb{G}_1$ randomly
		x, alpha = self.__group.random(ZR), self.__group.random(ZR) # generate $x, \alpha \in \mathbb{Z}_r$ randomly
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(x, G1) # $H_2: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H3 = lambda x:self.__group.hash(x, ZR) # $H_3: \{0, 1\}^* \rightarrow \mathbb{Z}_r$
		H4 = lambda x:self.__group.hash(x, G1) # $H_4: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H5 = lambda x:self.__group.hash(x, G1) # $H_5: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H6 = lambda x:self.__group.hash(x, G1) # $H_6: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		H7 = lambda x:self.__group.hash(x, G1) # $H_7: \{0, 1\}^* \rightarrow \mathbb{G}_1$
		y = g ** x # $y \gets g^x$
		self.__mpk = (g, h, H1, H2, H3, H4, H5, H6, H7, y) # $ \textit{mpk} \gets (G, G_T, q, g, e, h, H_1, H_2, H_3, H_4, H_5, H_6, H_7, y)$
		self.__msk = (x, alpha) # $\textit{msk} \gets (x, \alpha)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def DKGen(self:object, idR:bytes) -> tuple: # $\textbf{DKGen}(\textit{id}_R) \rightarrow \textit{dk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, bytes): # type check
			id_R = idR
		else:
			id_R = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("DKGen: The variable $\\textit{id}_R$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[2]
		x, alpha = self.__msk
		
		# Scheme #
		dk_id_R1 = H1(id_R) ** x # $\textit{dk}_{\textit{id}_R, 1} \gets H_1(\textit{id}_R)^x$
		dk_id_R2 = H1(id_R) ** alpha # $\textit{dk}_{\textit{id}_R, 2} \gets H_1(\textit{id}_R)^\alpha$
		dk_id_R = (dk_id_R1, dk_id_R2) # $\textit{dk}_{\textit{id}_R} \gets (\textit{dk}_{\textit{id}_R, 1}, \textit{dk}_{\textit{id}_R, 2})$
		
		# Return #
		return dk_id_R # \textbf{return} $\textit{dk}_{\textit{id}_R}$
	def EKGen(self:object, idS:bytes) -> Element: # $\textbf{EKGen}(\textit{id}_S) \rightarrow \textit{ek}_{\textit{id}_S}$
		# Check #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(idS, bytes): # type check
			id_S = idS
		else:
			id_S = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("EKGen: The variable $\\textit{id}_S$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		
		# Unpack #
		H2 = self.__mpk[3]
		alpha = self.__msk[-1]
		
		# Scheme #
		ek_id_S = H2(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_2(\textit{id}_S)^\alpha$
		
		# Return #
		return ek_id_S # \textbf{return} $\textit{ek}_{\textit{id}_S}$
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
			if isinstance(dkid2, tuple) and len(dkid2) == 2 and all(isinstance(ele, Element) for ele in dkid2): # hybrid check
				dk_id_2 = dkid2
			else:
				dk_id_2 = self.DKGen(id_2)
				print("ReEKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated accordingly. ")
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("ReEKGen: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			ek_id_2 = self.EKGen(id_2)
			print("ReEKGen: The variable $\\textit{ek}_{\\textit{id}_2}$ has been generated accordingly. ")
			dk_id_2 = self.DKGen(id_2)
			print("ReEKGen: The variable $\\textit{dk}_{\\textit{id}_2}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("ReEKGen: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(id3, bytes): # type check
			id_3 = id3
		else:
			id_3 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
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
			H7(self.__group.serialize(K) + id_2 + id_3 + self.__group.serialize(N)) * dk_id_2[1] # H_7(K || \textit{id}_2 || \textit{id}_3 || N) \cdot \textit{dk}_{\textit{id}_2, 2}
		) # )$
		rk = (N, rk1, rk2, rk3) # $\textit{rk} \gets (N, \textit{rk}_1, \textit{rk}_2, \textit{rk}_3)$
		
		# Return #
		return rk # \textbf{return} $\textit{rk}$
	def Enc(self:object, ekid1:Element, id2:Element, message:int|bytes) -> object: # $\textbf{Enc}(\textit{ek}_{\textit{id}_1}, \textit{id}_2, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(ekid1, Element): # type check
			ek_id_1 = ekid1
		else:
			ek_id_1 = self.EKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"))
			print("Enc: The variable $\\textit{ek}_{\\textit{id}_1}$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Enc: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(message, int) and message >= 0: # type check
			m = message & self.__operand
			if message != m:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			m = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			m = int.from_bytes(b"SchemeIBPRME", byteorder = "big")
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemeIBPRME\". ")
		
		# Unpack #
		g, h, H1, H3, H4, H5, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[-1]
		
		# Scheme #
		sigma = self.__group.random(G1) # generate $\sigma \in \mathbb{G}_1$ randomly
		eta = self.__group.random(GT) # generate $\eta \in \mathbb{G}_T$ randomly
		r = H3(m.to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") + self.__group.serialize(sigma) + self.__group.serialize(eta)) # $r \gets H_3(m || \sigma || \eta)$
		ct1 = h ** r # $\textit{ct}_1 \gets h^r$
		ct2 = g ** r # $\textit{ct}_2 \gets g^r$
		ct3 = (
			int.from_bytes(m.to_bytes(ceil(self.__group.secparam / 8), byteorder = "big") + self.__group.serialize(sigma), byteorder = "big")
			^ int.from_bytes(self.__group.serialize(H4(pair(y, H1(id_2)) ** r)), byteorder = "big")
			^ int.from_bytes(self.__group.serialize(H4(eta)), byteorder = "big")
		) # $\textit{ct}_3 \gets (m || \sigma) \oplus H_4(e(y, H_1(\textit{id}_2))^r) \oplus H_4(\eta)$
		ct4 = eta * pair(ek_id_1, H1(id_2)) # $\textit{ct}_4 \gets \eta \cdot e(\textit{ek}_{\textit{id}_1}, H_1(\textit{id}_2))$
		ct5 = (																																												\
			H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + ct3.to_bytes(ceil(self.__group.secparam / 8) + len(self.__group.serialize(self.__group.random(G1))), byteorder = "big") + self.__group.serialize(ct4)) ** r		\
		) # $\textit{ct}_5 \gets H_5(\textit{ct}_1 || \textit{ct}_2 || \textit{ct}_3 || \textit{ct}_4)^r$
		ct = (ct1, ct2, ct3, ct4, ct5) # $\textit{ct} \gets (\textit{ct}_1, \textit{ct}_2, \textit{ct}_3, \textit{ct}_4, \textit{ct}_5)$
		
		# Return #
		return ct # \textbf{return} $\textit{ct}$
	def ReEnc(self:object, cipherText:tuple, reKey:tuple) -> tuple|bool: # $\textbf{ReEnc}(\textit{ct}, \textit{rk}) \rightarrow \textit{ct}'$
		# Check #
		if not self.__flag:
			print("ReEnc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``ReEnc`` subsequently. ")
			self.Setup()
		id2Generated = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and all(isinstance(ele, Element) for ele in cipherText[:2]) and isinstance(cipherText[2], int) and all(isinstance(ele, Element) for ele in cipherText[3:]): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.EKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), id2Generated, int.from_bytes(b"SchemeIBPRME", byteorder = "big"))
			print("ReEnc: The variable $\\textit{ct}$ should be a tuple containing 4 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPRME\". ")
		if isinstance(reKey, tuple) and len(reKey) == 4 and all(isinstance(ele, Element) for ele in reKey): # hybrid check
			rk = reKey
		else:
			rk = self.ReEKGen(																														\
				self.EKGen(id2Generated), self.DKGen(id2Generated), randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big"), 	\
				id2Generated, randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")										\
			)
			print("ReEnc: The variable $\\textit{rk}$ should be a tuple containing 4 elements but it is not, which has been generated randomly. ")
		del id2Generated
		
		# Unpack #
		g, h, H1, H2, H5, H6, H7, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[-1]
		x = self.__msk[0]
		N, rk1, rk2, rk3 = rk
		ct1, ct2, ct3, ct4, ct5 = ct
		
		# Scheme #
		if (																																																	\
			pair(ct1, g) == pair(h, ct2)																																											\
			and pair(ct1, H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + ct3.to_bytes(ceil(self.__group.secparam / 8) + len(self.__group.serialize(self.__group.random(G1))), byteorder = "big") + self.__group.serialize(ct4))) == pair(h, ct5)	\
		): # \textbf{if} $e(\textit{ct}_1, g) = e(h, \textit{ct}_2) \land e(\textit{ct}_1, H_5(\textit{ct}_1 || \textit{ct}_2 || \textit{ct}_3 || \textit{ct}_4)) = e(h, \textit{ct}_5)$ \textbf{then}
			ct4Prime = ct4 / rk3 # \quad$\textit{ct}_4' \gets \frac{\textit{ct}_4}{\textit{rk}_3}$
			ct6 = rk1 # \quad$\textit{ct}_6 \gets \textit{rk}_1$
			ct7 = pair(rk2, ct2) / pair(ct1, rk1) # \quad$\textit{ct}_7 \gets \frac{e(\textit{rk}_2, \textit{ct}_2)}{e(\textit{ct}_1, \textit{rk}_1)}$
			ctPrime = (ct2, ct3, ct4Prime, ct6, ct7, N) # \quad$\textit{ct}' \gets (\textit{ct}_2, \textit{ct}_3, \textit{ct}_4', \textit{ct}_6, \textit{ct}_7, N)$
		else: # \textbf{else}
			ctPrime = False # \quad$\textit{ct}' \gets \perp$
		# \textbf{end if}
		
		# Return #
		return ctPrime # \textbf{return} $\textit{ct}'$
	def Dec1(self:object, dkid2:tuple, id1:Element, cipherText:tuple) -> int|bool: # $\textbf{Dec}_1(\textit{dk}_{\textit{id}_2}, \textit{id}_1, \textit{ct}) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec1: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec1`` subsequently. ")
			self.Setup()
		id2Generated = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
		if isinstance(dkid2, tuple) and len(dkid2) == 2 and all(isinstance(ele, Element) for ele in dkid2): # hybrid check
			dk_id_2 = dkid2
		else:
			dk_id_2 = self.DKGen(id2Generated)
			print("Dec1: The variable $\\textit{dk}_{\\textit{id}_2}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec1: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 5 and all(isinstance(ele, Element) for ele in cipherText[:2]) and isinstance(cipherText[2], int) and all(isinstance(ele, Element) for ele in cipherText[3:]): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.EKGen(randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")), id2Generated, int.from_bytes(b"SchemeIBPRME", byteorder = "big"))
			print("Dec1: The variable $\\textit{ct}$ should be a tuple containing 4 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPRME\". ")
		del id2Generated
		
		# Unpack #
		g, h, H1, H2, H3, H4, H5, H6, H7, y = self.__mpk
		x = self.__msk[0]
		ct1, ct2, ct3, ct4, ct5 = ct
		
		# Scheme #
		if (																																																		\
			pair(ct1, g) == pair(h, ct2)																																												\
			and pair(ct1, H5(self.__group.serialize(ct1) + self.__group.serialize(ct2) + ct3.to_bytes(ceil(self.__group.secparam / 8) + len(self.__group.serialize(self.__group.random(G1))), byteorder = "big") + self.__group.serialize(ct4))) == pair(h, ct5)		\
		): # \textbf{if} $e(\textit{ct}_1, g) = e(h, \textit{ct}_2) \land e(\textit{ct}_1, H_5(\textit{ct}_1 || \textit{ct}_2 || \textit{ct}_3 || \textit{ct}_4)) = e(h, \textit{ct}_5)$ \textbf{then}
			V = pair(dk_id_2[1], H2(id_1)) # \quad$V \gets e(\textit{dk}_{\textit{id}_2, 2}, H_2(\textit{id}_1))$
			etaPrime = ct4 / V # \quad$\eta' \gets \frac{\textit{ct}_4}{V}$
			ct3_H4_H4 = (																													\
				int.from_bytes(ct3.to_bytes(ceil(self.__group.secparam / 8) + len(self.__group.serialize(self.__group.random(G1))), byteorder = "big"), byteorder = "big")	\
				^ int.from_bytes(self.__group.serialize(H4(pair(dk_id_2[0], ct2))), byteorder = "big")															\
				^ int.from_bytes(self.__group.serialize(H4(etaPrime)), byteorder = "big")																	\
			) # $\quad m || \sigma \gets \textit{ct}_3 \oplus H_4(e(\textit{dk}_{\textit{id}_2, 1}, \textit{ct}_2)) \oplus H_4(\eta')$
			token1, token2 = ceil(self.__group.secparam / 8), len(self.__group.serialize(self.__group.random(G1)))
			ct3_H4_H4 = ct3_H4_H4.to_bytes(token1 + token2, byteorder = "big")
			r = H3(ct3_H4_H4 + self.__group.serialize(etaPrime)) # \quad$r \gets H_3((\textit{ct}_3 \oplus H_4(e(\textit{dk}_{\textit{id}_2, 1})) \oplus H_4(\eta')) || \eta')$
			if g ** r != ct2: # \quad\textbf{if} $g^r = \textit{ct}_2$ \textbf{then}
				m = False # \quad\quad$m \gets \perp$
			else:
				m = int.from_bytes(ct3_H4_H4[:token1], byteorder = "big")
			# \quad\textbf{end if}
		else: # \textbf{else}
			m = False # \quad$m \gets \perp$
		# \textbf{end if}
		
		# Return #
		return m # \textbf{return} $m$
	def Dec2(self:object, dkid3:tuple, id1:Element, id2:Element, id3:Element, cipherTextPrime:tuple|bool) -> int|bool: # $\textbf{Dec}_2(\textit{dk}_{\textit{id}_3}, \textit{id}_1, \textit{id}_2, \textit{id}_3, \textit{ct}') \rightarrow m'$
		# Check #
		if not self.__flag:
			print("Dec2: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec2`` subsequently. ")
			self.Setup()
		if isinstance(id3, bytes): # type check
			id_3 = id3
			if isinstance(dkid3, tuple) and len(dkid3) == 2 and all(isinstance(ele, Element) for ele in dkid3): # hybrid check
				dk_id_3 = dkid3
			else:
				dk_id_3 = self.DKGen(id_3)
				print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ should be a tuple containing 2 elements but it is not, which has been generated randomly. ")
		else:
			id_3 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_3$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
			dk_id_3 = self.DKGen(id_3)
			print("Dec2: The variable $\\textit{dk}_{\\textit{id}_3}$ has been generated accordingly. ")
		if isinstance(id1, bytes): # type check
			id_1 = id1
		else:
			id_1 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_1$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(id2, bytes): # type check
			id_2 = id2
		else:
			id_2 = randbelow(1 << self.__group.secparam).to_bytes(ceil(self.__group.secparam / 8), byteorder = "big")
			print("Dec2: The variable $\\textit{id}_2$ should be a ``bytes`` object but it is not, which has been generated randomly. ")
		if isinstance(cipherTextPrime, tuple) and len(cipherTextPrime) == 6 and isinstance(cipherTextPrime[0], Element) and isinstance(cipherTextPrime[1], int) and all(isinstance(ele, Element) for ele in cipherTextPrime[2:]): # hybrid check
			ctPrime = cipherTextPrime
		elif isinstance(cipherTextPrime, bool):
			return False
		else:
			ctPrime = self.ReEnc(self.Enc(self.EKGen(id_1), id_2, int.from_bytes(b"SchemeIBPRME", byteorder = "big")), self.ReEKGen(self.EKGen(id_2), self.DKGen(id_2), id_1, id_2, id_3))
			print("Dec2: The variable $\\textit{ct}'$ should be a tuple containing 5 elements and an integer but it is not, which has been generated with $m$ set to b\"SchemeIBPRME\". ")
		
		# Unpack #
		g, h, H1, H2, H3, H4, H6, H7, y = self.__mpk[0], self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[7], self.__mpk[8], self.__mpk[-1]
		x = self.__msk[0]
		ct2, ct3, ct4Prime, ct6, ct7, N = ctPrime
		
		# Scheme #
		V = pair(dk_id_3[1], H2(id_2)) # $V \gets e(\textit{dk}_{\textit{id}_3, 2}, H_2(\textit{id}_2))$
		etaPrime = ct4Prime * pair(H2(id_1), H7(self.__group.serialize(V) + id2 + id3 + self.__group.serialize(N))) # $\eta' \gets \textit{ct}_4' \cdot e(H_2(\textit{id}_1), H_7(V || \textit{id}_2 || \textit{id}_3 || N))$
		R = ct7 / pair(H6(pair(dk_id_3[0], ct6)), ct2) # $R \gets \frac{\textit{ct}_7}{e(H_6(e(\textit{dk}_{\textit{id}_3, 1}, \textit{ct}_6), \textit{ct}_2)}$
		ct3_H4_H4 = (																													\
			int.from_bytes(ct3.to_bytes(ceil(self.__group.secparam / 8) + len(self.__group.serialize(self.__group.random(G1))), byteorder = "big"), byteorder = "big")	\
			^ int.from_bytes(self.__group.serialize(H4(R)), byteorder = "big")																		\
			^ int.from_bytes(self.__group.serialize(H4(etaPrime)), byteorder = "big")																	\
		) # $m || \sigma \gets \textit{ct}_3 \oplus H_4(R) \oplus H_4(\eta')$
		token1, token2 = ceil(self.__group.secparam / 8), len(self.__group.serialize(self.__group.random(G1)))
		ct3_H4_H4 = ct3_H4_H4.to_bytes(token1 + token2, byteorder = "big")
		r = H3(ct3_H4_H4 + self.__group.serialize(etaPrime)) # $r \gets H_3((\textit{ct}_3 \oplus H_4(R) \oplus H_4(\eta')) || \eta')$
		if g ** r != ct2: # \textbf{if} $g^r \neq \textit{ct}_2$ \textbf{then}
			m = False # \quad$m \gets \perp$
		else:
			m = ct3_H4_H4[:token1]
		# \textbf{end if}
		m = int.from_bytes(m, byteorder = "big")
		
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
		return (																																													\
			([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int) else [curveType if isinstance(curveType, str) else None, None])	\
			+ [round if isinstance(round, int) else None] + [False] * 4 + [-1] * 20																																\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(round, int) and round >= 0:
		print("round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBPRME = SchemeIBPRME(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBPRME.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DKGen #
	startTime = perf_counter()
	id_2 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	id_3 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	dk_id_2 = schemeIBPRME.DKGen(id_2)
	dk_id_3 = schemeIBPRME.DKGen(id_3)
	endTime = perf_counter()
	timeRecords.append((endTime - startTime) / 2)
	
	# EKGen #
	startTime = perf_counter()
	id_1 = randbelow(1 << group.secparam).to_bytes(ceil(group.secparam / 8), byteorder = "big")
	ek_id_1 = schemeIBPRME.EKGen(id_1)
	ek_id_2 = schemeIBPRME.EKGen(id_2)
	endTime = perf_counter()
	timeRecords.append((endTime - startTime) / 2)
	
	# ReEKGen #
	startTime = perf_counter()
	rk = schemeIBPRME.ReEKGen(ek_id_2, dk_id_2, id_1, id_2, id_3)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = int.from_bytes(b"SchemeIBPRME", byteorder = "big")
	ct = schemeIBPRME.Enc(ek_id_1, id_2, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# ReEnc #
	startTime = perf_counter()
	ctPrime = schemeIBPRME.ReEnc(ct, rk)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec1 #
	startTime = perf_counter()
	m = schemeIBPRME.Dec1(dk_id_2, id_1, ct)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec2 #
	startTime = perf_counter()
	mPrime = schemeIBPRME.Dec2(dk_id_3, id_1, id_2, id_3, ctPrime)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(ctPrime, bool), not isinstance(m, bool) and message == m, not isinstance(mPrime, bool) and message == mPrime]
	spaceRecords = [																																					\
		schemeIBPRME.getLengthOf(group.random(ZR)), schemeIBPRME.getLengthOf(group.random(G1)), schemeIBPRME.getLengthOf(group.random(GT)), 								\
		schemeIBPRME.getLengthOf(mpk), schemeIBPRME.getLengthOf(msk), schemeIBPRME.getLengthOf(ek_id_1), schemeIBPRME.getLengthOf(ek_id_2), 								\
		schemeIBPRME.getLengthOf(dk_id_2), schemeIBPRME.getLengthOf(dk_id_3), schemeIBPRME.getLengthOf(rk), schemeIBPRME.getLengthOf(ct), schemeIBPRME.getLengthOf(ctPrime)	\
	]
	del schemeIBPRME
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


def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, roundCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
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
					outputFilePath = parser.handlePath(input("Please specify a new output file path or leave it empty for console output: "))
				except:
					print()
		del parser
		
		# Parameters #
	curveTypes = (("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
	roundCount, filePath = 100, "SchemeIBPRME.xlsx"
	queries = ["curveType", "secparam", "roundCount"]
	validators = ["isSystemValid", "isReEKGenPassed", "isDec1Passed", "isDec2Passed"]
	metrics = [																						\
		"Setup (s)", "DKGen (s)", "EKGen (s)", "ReEKGen (s)", "Enc (s)", "ReEnc (s)", "Dec1 (s)", "Dec2 (s)", 			\
		"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 										\
		"mpk (B)", "msk (B)", "ek_id_1 (B)", "ek_id_2 (B)", "dk_id_2 (B)", "dk_id_3 (B)", "rk (B)", "ct (B)", "ct\' (B)"	\
	]
	
	# Scheme #
	qLength, columns, results = len(queries), queries + validators + metrics, []
	length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
	try:
		for curveType in curveTypes:
			average = conductScheme(curveType, round = 0)
			for round in range(1, roundCount):
				result = conductScheme(curveType, round = round)
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
			print("Saver: \n{0}\n".format(results))
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
						print("Saver: \n{0}\n\nFailed to save the results to \"{1}\" due to the following exception(s). \n\t{2}".format(results, filePath, e))
			else:
				print("Saver: \n{0}\n\nThe overwriting is canceled by users. ".format(results))
		else:
			print("Saver: \n{0}\n\nFailed to save the results to \"{1}\" since the parent folder was not created successfully. ".format(results, filePath))
	else:
		print("The results are empty. ")
	
	# End #
	errorLevel = EXIT_SUCCESS if results and all(all(tuple(r == roundCount for r in result[3:7]) + tuple(r > 0 for r in result[7:length])) for result in results) else EXIT_FAILURE
	try:
		if isinstance(sleepingTime, float) and 0 <= sleepingTime < float("inf"):
			print("Please wait for the countdown ({0} second(s)) to end, or exit the program manually like pressing the \"Ctrl + C\" ({1}). \n".format(sleepingTime, errorLevel))
			sleep(sleepingTime)
		else:
			print("Please press the enter key to exit ({0}). ".format(errorLevel))
			input()
	except:
		print()
	return errorLevel



if "__main__" == __name__:
	exit(main())