import os
from sys import argv, exit
from hashlib import md5, sha1, sha224, sha256, sha384, sha512
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


class Parser:
	def __init__(self:object, arguments:tuple|list) -> object:
		self.__arguments = tuple(argument for argument in arguments if isinstance(argument, str)) if isinstance(arguments, (tuple, list)) else ()
		self.__schemeName = "SchemeIBMETR" # os.path.splitext(os.path.basename(__file__))[0]
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
		print("This is the official implementation of the IBMETR cryptography scheme in Python programming language based on the Python charm library. \n")
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
		if isinstance(results, (tuple, list)) and all(isinstance(result, (tuple, list)) and all(isinstance(r, (None, float, int, str)) for r in result) for result in results):
			if self.__outputFilePath in ("", "."):
				print("Saver: {0}".format({"columns":self.__columns, "results":results}))
				return True
			else:
				flag, extension = True, self.__outputFilePath.split(".")[-1]
				extensionUpper = extension.upper()
				while True: # try our best to avoid ``KeyboardInterrupt`` when writing the output file
					if flag and extensionUpper in ("CSV", "XLSX"):
						try:
							df = __import__("pandas").DataFrame(results, columns = self.__columns)
							if "xlsx" == extension: # ``to_excel`` only supports the lower-case ``.xlsx`` extension
								df.to_excel(self.__outputFilePath, index = False, float_format = self.__floatFormat)
							else:
								df.to_csv(self.__outputFilePath, index = False, float_format = self.__floatFormat, encoding = self.__encoding)
							print("Saver: Successfully saved the results to \"{0}\" in the {1} format. ".format(self.__outputFilePath, extensionUpper))
							return True
						except KeyboardInterrupt:
							continue
						except BaseException as e:
							flag = False
							print("Saver: Failed to save the results to \"{0}\" in the {1} format. Exceptions are as follows. \n\t{2}".format(	\
								self.__outputFilePath, extensionUpper, e									\
							))
					else:
						try:
							with open(self.__outputFilePath, "wt", encoding = self.__encoding) as f:
								if "PY" == extensionUpper:
									f.write(str({"columns":self.__columns, "results":results}))
								elif "TEX" == extensionUpper:
									maxLength = max(len(self.__columns) if isinstance(self.__columns, (tuple, list)) else 0, max(len(result) for result in results))
									f.write("\\documentclass[a4paper]{article}\n\\setlength{\\parindent}{0pt}\n\\usepackage{booktabs}\n\n\\begin{document}\n\n")
									f.write("\\begin{table}\n\t\\caption{The comparison results. }\n\t\\begin{tabular}{")
									f.write("c" * maxLength)
									f.write("}\n\t\t\\toprule\n\t\t\t")
									if isinstance(self.__columns, (tuple, list)) and self.__columns:
										f.write(" & ".join("\\textbf{{{0}}}".format(column) for column in self.__columns))
										if len(columns) < maxLength:
											f.write(" & \\textbf{~}" * (maxLength - len(result)))
									else:
										f.write(" & ".join(("\\textbf{~}", ) * maxLength))
									f.write(" \\\\\n\t\t\\midrule\n")
									for result in results:
										if result:
											f.write("\t\t\t")
											f.write(" & ".join(result))
											if len(result) < maxLength:
												f.write(" & ~" * (maxLength - len(result)))
											f.write(" \\\\\n")
									f.write("\t\t\\bottomrule\n\t\\end{tabular}\n\\end{table}\n\n\\end{document}")
								else:
									if isinstance(self.__columns, (tuple, list)) and self.__columns:
										f.write("\t".join(self.__columns))
										if results:
											f.write("\n")
									f.write("\n".join("\t".join(str(r) for r in result)) for result in results if result)
							print("Saver: Successfully saved the results to \"{0}\" in the {1} format. ".format(self.__outputFilePath, extensionUpper))
							return True
						except KeyboardInterrupt:
							continue
						except BaseException as e:
							if flag:
								print("Saver: Failed to save the results to \"{0}\" due to the following exception(s). \n\t{1}".format(self.__outputFilePath, e))
							else:
								print("\t{0}".format(e))
							print("Saver: {0}".format({"columns":self.__columns, "results":results}))
							return False
		else:
			print("Saver: The results are invalid. ")
			return False

class SchemeIBMETR:
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
	def __product(self:object, vec:tuple|list|set) -> Element:
		if isinstance(vec, (tuple, list, set)) and vec and all(isinstance(ele, Element) for ele in vec):
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
		p = self.__group.order() # $p \gets \|\mathbb{G}\|$
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		H1 = lambda x:self.__group.hash(self.__group.serialize(x), G1) # $H_1:\{0, 1\}^* \rightarrow \mathbb{G}_1$
		H2 = lambda x:self.__group.hash(self.__group.serialize(x), G2) # $H_2:\{0, 1\}^* \rightarrow \mathbb{G}_2$
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
			HHat = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest() * (((self.__group.secparam - 1) >> 9) + 1), byteorder = "big") & self.__operand # $\hat{H}: \{0, 1\}^* \rightarrow \{0, 1\}^\lambda$
			print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
		g0, g1 = self.__group.random(G1), self.__group.random(G1) # generate $g_0, g_1 \in \mathbb{G}_1$ randomly
		w, alpha, t1, t2 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $w, alpha, t_1, t_2 \in \mathbb{Z}_r$
		Omega = pair(g, g) ** w # $\Omega \gets e(g, g)^w$
		v1 = g ** t1 # $v \gets g^{t_1}$
		v2 = g ** t2 # $v \gets g^{t_2}$
		self.__mpk = (p, g, g0, g1, v1, v2, Omega, H1, H2, HHat) # $\textit{mpk} \gets (p, g, g_0, g_1, v_1, v_2, \Omega, H_1, H_2, \hat{H})$
		self.__msk = (w, alpha, t1, t2) # $\textit{msk} \gets (w, \alpha, t_1, t_2)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, idS:Element) -> Element: # $\textbf{EKGen}(\textit{id}_S) \rightarrow \textit{ek}_{\textit{id}_S}$
		# Check #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(idS, Element) and idS.type == ZR: # type check
			id_S = idS
		else:
			id_S = self.__group.random(ZR)
			print("EKGen: The variable $\\textit{id}_S$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1 = self.__mpk[-3]
		alpha = self.__msk[1]
		
		# Scheme #
		ek_id_S = H1(id_S) ** alpha # $\textit{ek}_{\textit{id}_S} \gets H_1(\textit{id}_S)$
		
		# Return #
		return ek_id_S # \textbf{return} $\textit{ek}_{\textit{id}_S}$
	def DKGen(self:object, idR:Element) -> tuple: # $\textbf{DKGen}(\textit{id}_R) \rightarrow \textit{dk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("DKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
		else:
			id_R = self.__group.random(ZR)
			print("DKGen: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1, H2 = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[-2]
		w, alpha, t1, t2 = self.__msk
		
		# Scheme #
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_r$ randomly
		dk0 = H2(id_R) ** alpha # $\textit{dk}_0 \gets H_2(\textit{id}_R)^\alpha$
		dk1 = g ** r # $\textit{dk}_1 \gets g^r$
		dk2 = g ** (-(w / t1)) * (g0 * g1 ** id_R) ** (-(r / t1)) # $\textit{dk}_2 \gets g^{-\frac{w}{t_1}}(g_0 g_1^{\textit{id}_R})^{-\frac{r}{t_1}}$
		dk3 = g ** (-(w / t2)) * (g0 * g1 ** id_R) ** (-(r / t2)) # $\textit{dk}_3 \gets g^{-\frac{w}{t_2}}(g_0 g_1^{\textit{id}_R})^{-\frac{r}{t_2}}$
		dk_id_R = (dk0, dk1, dk2, dk3) # $\textit{dk}_{\textit{ID}_R} \gets (\textit{dk}_0, \textit{dk}_1, \textit{dk}_2, \textit{dk}_3)$
		
		# Return #
		return dk_id_R # \textbf{return} $\textit{dk}_{\textit{id}_R}$
	def TKGen(self:object, idR:Element) -> tuple: # $\textbf{TKGen}(\textit{id}_R) \rightarrow \textit{tk}_{\textit{id}_R}$
		# Check #
		if not self.__flag:
			print("TKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``TKGen`` subsequently. ")
			self.Setup()
		if isinstance(idR, Element) and idR.type == ZR: # type check
			id_R = idR
		else:
			id_R = self.__group.random(ZR)
			print("TKGen: The variable $\\textit{id}_R$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1 = self.__mpk[1], self.__mpk[2], self.__mpk[3]
		t1, t2 = self.__msk[2], self.__msk[3]
		
		# Scheme #
		k = self.__group.random(ZR) # generate $k \in \mathbb{Z}_r$ randomly
		tk1 = g ** k # $\textit{tk}_1 \gets g^k$
		tk2 = g ** (1 / t1) * (g0 * g1 ** id_R) ** (-(k / t1)) # $\textit{tk}_2 \gets g^{\frac{1}{t_1}}(g_0 g_1^{\textit{id}_R})^{-\frac{k}{t_1}}$
		tk3 = g ** (1 / t2) * (g0 * g1 ** id_R) ** (-(k / t2)) # $\textit{tk}_3 \gets g^{\frac{1}{t_2}}(g_0 g_1^{\textit{id}_R})^{-\frac{k}{t_2}}$
		tk_id_R = (tk1, tk2, tk3) # $\textit{tk}_{\textit{ID}_R} \gets (\textit{tk}_1, \textit{tk}_2, \textit{tk}_3)$
		
		# Return #
		return tk_id_R # \textbf{return} $\textit{tk}_{\textit{id}_R}$
	def Enc(self:object, ekidS:Element, idRev:Element, message:int|bytes) -> Element: # $\textbf{Enc}(\textit{ek}_{\textit{id}_S}, \textit{id}_\textit{Rev}, m) \rightarrow \textit{ct}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(ekidS, Element): # type check
			ek_id_S = ekidS
		else:
			ek_id_S = self.EKGen(self.__group.random(ZR))
			print("Enc: The variable $\\textit{ek}_{\\textit{id}_S}$ should be an element but it is not, which has been generated randomly. ")
		if isinstance(idRev, Element) and idRev.type == ZR: # type check
			id_Rev = idRev
		else:
			id_Rev = self.__group.random(ZR)
			print("Enc: The variable $\\textit{id}_\textit{Rev}$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(message, int) and message >= 0: # type check
			m = message & self.__operand
			if message != m:
				print("Enc: The passed message (int) is too long, which has been cast. ")
		elif isinstance(message, bytes):
			m = int.from_bytes(message, byteorder = "big") & self.__operand
			if len(message) << 3 > self.__group.secparam:
				print("Enc: The passed message (bytes) is too long, which has been cast. ")
		else:
			m = int.from_bytes(b"SchemeIBMETR", byteorder = "big")
			print("Enc: The variable $m$ should be an integer or a ``bytes`` object but it is not, which has been defaulted to b\"SchemeIBMETR\". ")
		
		# Unpack #
		g, g0, g1, v1, v2, Omega, H2, HHat = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[-2], self.__mpk[-1]
		
		# Scheme #
		s1, s2, beta = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $s_1, s_2, beta \in \mathbb{Z}_r$ randomly
		s = s1 + s2 # $s = s_1 + s_2$
		R = Omega ** -s # $R = \Omega^{-s}$
		T = g ** beta # $T \gets g^\beta$
		K = pair(H2(id_Rev), ek_id_S * T) # $K \gets e(H_2(\textit{id}_\textit{Rev}), \textit{ek}_{\textit{id}_S} \cdot T)$
		ct0 = HHat(R) ^ HHat(K) ^ m # $\textit{ct}_0 \gets \hat{H}(R) \oplus \hat{H}(K) \oplus m$
		ct1 = (g0 * g1 ** id_Rev) ** s # $\textit{ct}_1 \gets (g_0 g_1^{\textit{id}_\textit{Rev}})^s$
		ct2 = v1 ** s1 # $\textit{ct}_2 \gets v_1^{s_1}$
		ct3 = v2 ** s2 # $\textit{ct}_3 \gets v_2^{s_2}$
		V = pair(g, g) ** s # $e(g, g)^s$
		ct = (ct0, ct1, ct2, ct3, T, V) # $\textit{ct} \gets (\textit{ct}_0, \textit{ct}_1, \textit{ct}_2, \textit{ct}_3, T, V)$
		
		# Return #
		return ct # \textbf{return} $\textit{ct}$
	def Dec(self:object, dkidR:tuple, idRev:Element, idSnd:Element, cipherText:tuple) -> bytes: # $\textbf{Dec}(\textit{dk}_{\textit{id}_R}, \textit{id}_\textit{Rev}, \textit{id}_\textit{Snd}, \textit{ct}) \rightarrow m$
		# Check #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if isinstance(idRev, Element) and idRev.type == ZR: # type check
			id_Rev = idRev
			if isinstance(dkidR, tuple) and len(dkidR) == 4 and all(isinstance(ele, Element) for ele in dkidR): # hybrid check
				dk_id_R = dkidR
			else:
				dk_id_R = self.DKGen(id_Rev)
				print("Dec: The variable $\\textit{dk}_{\\textit{id}_R}$ should be a tuple containing 4 elements but it is not, which has been generated accordingly. ")
		else:
			id_Rev = self.__group.random(ZR)
			print("Dec: The variable $\\textit{id}_\\textit{Rev}$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			dk_id_R = self.DKGen(id_Rev)
			print("Dec: The variable $\\textit{dk}_{\\textit{id}_R}$ has been generated accordingly. ")
		if isinstance(idSnd, Element) and idSnd.type == ZR: # type check
			id_Snd = idSnd
		else:
			id_Snd = self.__group.random(ZR)
			print("Dec: The variable $\\textit{id}_\textit{Snd}$ should be an element of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 6 and isinstance(cipherText[0], int) and all(isinstance(ele, Element) for ele in cipherText[1:]): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.__group.random(ZR), self.__group.random(ZR), int.from_bytes(b"SchemeIBMETR", byteorder = "big"))
			print("Dec: The variable $\\textit{ct}$ should be a tuple containing an integer and 5 elements but it is not, which has been generated randomly. ")
		
		# Unpack #
		H1, H2, HHat = self.__mpk[-3], self.__mpk[-2], self.__mpk[-1]
		dk0, dk1, dk2, dk3 = dk_id_R
		ct0, ct1, ct2, ct3, T = ct[0], ct[1], ct[2], ct[3], ct[4]
		
		# Scheme #
		RPrime = pair(dk1, ct1) * pair(dk2, ct2) * pair(dk3, ct3) # $R' \gets e(\textit{dk}_1, \textit{ct}_1) \cdot e(\textit{dk}_2, \textit{ct}_2) \cdot e(\textit{dk}_3, \textit{ct}_3)$
		KPrime = pair(dk0, H1(id_Snd)) * pair(H2(id_Rev), T) # $K' \gets e(\textit{dk}_0, H_1(\textit{id}_\textit{Snd})) \cdot e(H_2(\textit{id}_R), T)$
		m = ct0 ^ HHat(RPrime) ^ HHat(KPrime) # $m \gets \textit{ct}_0 \oplus \hat{H}(R') \oplus \hat{H}(K')$
		
		# Return #
		return m # \textbf{return} $m$
	def TVerify(self:object, tkidR:tuple, cipherText:tuple) -> bool: # $\textbf{TVerify}(\textit{tk}_{\textit{id}_R}, \textit{ct}) \rightarrow y, y \in \{0, 1\}$
		# Check #
		if not self.__flag:
			print("TVerify: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``TVerify`` subsequently. ")
			self.Setup()
		if isinstance(tkidR, tuple) and len(tkidR) == 3 and all(isinstance(ele, Element) for ele in tkidR): # hybrid check
			tk_id_R = tkidR
		else:
			tk_id_R = self.TKGen(self.__group.random(ZR))
			print("TVerify: The variable $\\textit{tk}_{\\textit{id}_R}$ should be a tuple containing 3 elements but it is not, which has been generated randomly. ")
		if isinstance(cipherText, tuple) and len(cipherText) == 6 and isinstance(cipherText[0], int) and all(isinstance(ele, Element) for ele in cipherText[1:]): # hybrid check
			ct = cipherText
		else:
			ct = self.Enc(self.__group.random(ZR), self.__group.random(ZR), int.from_bytes(b"SchemeIBMETR", byteorder = "big"))
			print("TVerify: The variable $\\textit{ct}$ should be a tuple containing an integer and 5 elements but it is not, which has been generated with $m$ set to b\"SchemeIBMETR\". ")
		
		# Unpack #
		tk1, tk2, tk3 = tk_id_R
		ct1, ct2, ct3, V = ct[1], ct[2], ct[3], ct[-1]
		
		# Scheme #
		pass
		
		# Return #
		return V == pair(tk1, ct1) * pair(tk2, ct2) * pair(tk3, ct3) # \textbf{return} $V = e(\textit{tk}_1, \textit{ct}_1) \cdot e(\textit{tk}_2, \textit{ct}_2) \cdot e(\textit{tk}_3, \textit{ct}_3)$
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
			+ [run if isinstance(run, int) else None] + [False] * 3 + [-1] * 16																																	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(run, int) and run >= 1:
		print("run =", run)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	schemeIBMETR = SchemeIBMETR(group)
	timeRecords = []
	
	# Setup #
	startTime = perf_counter()
	mpk, msk = schemeIBMETR.Setup()
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# EKGen #
	startTime = perf_counter()
	id_S = group.random(ZR)
	ek_id_S = schemeIBMETR.EKGen(id_S)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DKGen #
	startTime = perf_counter()
	id_R = group.random(ZR)
	dk_id_R = schemeIBMETR.DKGen(id_R)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# TKGen #
	startTime = perf_counter()
	tk_id_R = schemeIBMETR.TKGen(id_R)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = int.from_bytes(b"SchemeIBMETR", byteorder = "big")
	ct = schemeIBMETR.Enc(ek_id_S, id_R, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec #
	startTime = perf_counter()
	m = schemeIBMETR.Dec(dk_id_R, id_R, id_S, ct)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# TVerify #
	startTime = perf_counter()
	bRet = schemeIBMETR.TVerify(tk_id_R, ct)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, message == m, bRet]
	spaceRecords = [																																						\
		schemeIBMETR.getLengthOf(group.random(ZR)), schemeIBMETR.getLengthOf(group.random(G1)), schemeIBMETR.getLengthOf(group.random(GT)), schemeIBMETR.getLengthOf(mpk), 		\
		schemeIBMETR.getLengthOf(msk), schemeIBMETR.getLengthOf(ek_id_S), schemeIBMETR.getLengthOf(dk_id_R), schemeIBMETR.getLengthOf(tk_id_R), schemeIBMETR.getLengthOf(ct)	\
	]
	del schemeIBMETR
	print("Original:", message)
	print("Decrypted:", m)
	print("Is the scheme correct (message == m)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Is the tracing verified? {0}. ".format("Yes" if booleans[2] else "No"))
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
		validators = ("isSystemValid", "isSchemeCorrect", "isTracingVerified")
		metrics = (																						\
			"Setup (s)", "EKGen (s)", "DKGen (s)", "TKGen (s)", "Enc (s)", "Dec (s)", "TVerify (s)", 	\
			"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 									\
			"mpk (B)", "msk (B)", "EK (B)", "DK (B)", "TK' (B)", "CT (B)"								\
		)
	
		# Scheme #
		columns, qLength, results = queries + validators + metrics, len(queries), []
		length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
		saver = Saver(outputFilePath, columns)
		if saver.initialize():
			try:
				for curveType in curveTypes:
					averages = conductScheme(curveType, round = 0)
					for run in range(2, roundCount + 1):
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