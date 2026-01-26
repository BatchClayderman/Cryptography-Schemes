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


class Parser:
	def __init__(self:object, arguments:tuple|list) -> object:
		self.__arguments = tuple(argument for argument in arguments if isinstance(argument, str)) if isinstance(arguments, (tuple, list)) else ()
		self.__schemeName = "SchemeAAIBME" # os.path.splitext(os.path.basename(__file__))[0]
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
		print("This is the official implementation of the AA-IB-ME cryptography scheme in Python programming language based on the Python charm library. \n")
		print("Options (not case-sensitive): ")
		print("\t{0} [utf-8|utf-16|...]\t\tSpecify the encoding mode for CSV and TXT outputs. The default value is {1}. ".format(self.__formatOption(self.__optionE), self.__defaultE))
		print("\t{0}\t\tPrint this help document. ".format(self.__formatOption(self.__optionH)))
		print("\t{0} [.|./{1}.xlsx|./{1}.csv|...]\t\tSpecify the output file path, leaving it empty for console output. The default value is {2}. ".format(		\
			self.__formatOption(self.__optionO), self.__schemeName, self.__defaultO																				\
		))
		print("\t{0} [1|2|5|10|20|50|100|...]\t\tSpecify the round count, which must be a positive integer. The default value is {1}. ".format(self.__formatOption(self.__optionR), self.__defaultR))
		print(																																						\
			"\t{0} [0|0.1|1|10|...|inf]\t\tSpecify the waiting time before exiting, which should be non-negative. ".format(self.__formatOption(self.__optionT))		\
			+ "Passing nan, None, or inf requires users to manually press the enter key before exiting. The default value is {0}. ".format(self.__defaultT)			\
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
		if isinstance(coefficients, (tuple, list)) and coefficients and (																		\
			isinstance(x, Element) and all(isinstance(coefficient, Element) and coefficient.type == x.type for coefficient in coefficients)		\
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
		H1 = lambda x:self.__group.hash(x, G1) # $H_1: \{0, 1\}^* \rightarrow \mathbb{G}_1$
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
		return (self.__mpk, self.__msk) # \textbf{return} $(\textit{mpk}, \textit{msk})$
	def EKGen(self:object, IDA:tuple, _S:tuple) -> tuple: # $\textbf{EKGen}(\textit{ID}_A, S) \rightarrow \textit{ek}_{\textit{ID}_A}(S)$
		# Check #
		if not self.__flag:
			print("EKGen: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``EKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDA, tuple) and len(IDA) == self.__n and all([isinstance(ele, Element) and ele.type == ZR for ele in IDA]): # hybrid check
			ID_A = IDA
		else:
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("EKGen: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if isinstance(_S, tuple) and len(_S) == self.__d and all(isinstance(ele, int) and ele < self.__n for ele in _S):
			S = _S
		else:
			S = list(range(n))
			shuffle(S)
			S = tuple(sorted(S[:self.__d]))
			print("EKGen: The variable $S$ should be a tuple containing $d$ integers smaller than $n$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g3, uVec, TVec = self.__mpk[3], self.__mpk[10], self.__mpk[11]
		beta = self.__msk[1]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		H = lambda vec, ID:vec[0] * self.__product(			\
			vec[j + 1] ** ID[j] for j in range(self.__n)	\
		) # $H: (\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n)) \rightarrow \bm{u}_0\prod\limits_{j \in [1, n]} \bm{u}_j^{\textit{ID}_j}$
		rVec = tuple(self.__group.random(ZR) for _ in range(self.__n)) # generate $\vec{r} = (r_1, r_2, \cdots, r_n) \in \mathbb{Z}_r^n$ randomly
		coefficients = (beta, ) + tuple(self.__group.random(ZR) for _ in range(self.__d - 2)) + (self.__group.init(ZR, 1), )
		q = lambda x:self.__computePolynomial(x, coefficients) # generate a $(d - 1)$ degree polynominal $q(x)$ s.t. $q(0) = \beta$ randomly
		ek_ID_A = tuple(																												\
			(g3 ** q(self.__group.init(ZR, i)) * (H(uVec, ID_A) * TVec[i]) ** rVec[i], g ** rVec[i]) for i in range(self.__n)			\
		) # $\textit{ek}_{\textit{ID}_{A_i}} \gets (g_3^{q(i)} [H(\bm{u}', \textit{ID}_A)T'_i]^{r_i}, g^{r_i}), \forall i \in \{1, 2, \cdots, n\}$
		ek_ID_A_S = tuple(ek_ID_A[i] for i in S) # generate $\textit{ek}_{\textit{ID}_A}(S) \subset \textit{ek}_{\textit{ID}_A}$ s.t. $\|\textit{ek}_{\textit{ID}_A}(S)\| = d$ randomly
		
		# Return #
		return ek_ID_A_S # \textbf{return} $\textit{ek}_{\textit{ID}_A}(S)$
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
		H = lambda vec, ID:vec[0] * self.__product(			\
			vec[j + 1] ** ID[j] for j in range(self.__n)	\
		) # $H: (\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n)) \rightarrow \bm{u}_0\prod\limits_{j \in [1, n]} \bm{u}_j^{\textit{ID}_j}$
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
		dk_ID_B_SPrime = tuple(dk_ID_B[self.__d:]) # generate $\textit{dk}_{\textit{ID}_B}(S') \subset \textit{dk}_{\textit{ID}_B}$ s.t. $\|\textit{dk}_{\textit{ID}_B}(S')\| = d$ randomly
		
		# Return #
		return dk_ID_B_SPrime # \textbf{return} $\textit{dk}_{\textit{ID}_B}(S')$
	def Enc(self:object, ekIDAS:tuple, IDA:tuple, IDB:tuple, _S:tuple, message:Element) -> tuple: # $\textbf{Enc}(\textit{ek}_{\textit{ID}_A}(S), \textit{ID}_A, \textit{ID}_B, S, M) \rightarrow \textit{CT}$
		# Check #
		if not self.__flag:
			print("Enc: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(_S, tuple) and len(_S) == self.__d and all(isinstance(ele, int) and ele < self.__n for ele in _S):
			S = _S
		else:
			S = list(range(n))
			shuffle(S)
			S = tuple(sorted(S[:self.__d]))
			print("Enc: The variable $S$ should be a tuple containing $d$ integers smaller than $n$ but it is not, which has been generated randomly. ")
		if isinstance(IDA, tuple) and len(IDA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDA): # hybrid check
			ID_A = IDA
			if isinstance(ekIDAS, tuple) and len(ekIDAS) == self.__d and all(isinstance(ele[0], tuple) and isinstance(ele[1], tuple) and len(ele[0]) == len(ele[1]) == 2 for ele in ekIDAS): # hybrid check
				ek_ID_A_S = ekIDAS
			else:
				ek_ID_A_S = self.EKGen(ID_A, S)
				print("Enc: The variable $\\textit{ek}_{\\textit{ID}_A}(S)$ should be a tuple containing $d$ tuples but it is not, which has been generated accordingly. ")
		else:
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Enc: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			ek_ID_A_S = self.EKGen(ID_A, S)
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
		Y1, Y2, v1, v2, v3, v4, uVec, TVec, uPrimeVec, TPrimeVec, H1 = self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7], self.__mpk[8], self.__mpk[9], self.__mpk[10], self.__mpk[11], self.__mpk[12], self.__mpk[13], self.__mpk[14]
		
		# Scheme #
		g = self.__group.init(G1, 1) # $g \gets 1_{\mathbb{G}_1}$
		H = lambda vec, ID:vec[0] * self.__product(			\
			vec[j + 1] ** ID[j] for j in range(self.__n)	\
		) # $H: (\bm{u} \gets (\bm{u}_0, \bm{u}_1, \cdots, \bm{u}_n), \textit{ID} \gets (\textit{ID}_1, \textit{ID}_2, \cdots, \textit{ID}_n)) \rightarrow \bm{u}_0\prod\limits_{j \in [1, n]} \bm{u}_j^{\textit{ID}_j}$
		SPrimePrime = list(range(self.__n))
		shuffle(SPrimePrime)
		SPrimePrime = tuple(sorted(SPrimePrime[:self.__d])) # generate $S'' \subset [1, n]$ s.t. $\|S''\| = d$ randomly
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
		zVec = tuple(self.__group.random(ZR) for _ in range(self.__d)) # generate $\vec{z} = (z_1, z_2, \cdots, z_n) \in \mathbb{Z}_r^d$ randomly
		zPrimeVec = tuple(self.__group.random(ZR) for _ in range(self.__d)) # generate $\vec{z}' = (z'_1, z'_2, \cdots, z'_n) \in \mathbb{Z}_r^d$ randomly
		C6Vec = tuple(g ** zPrimeVec[i] for i, j in enumerate(S)) # $C_{6, i} \gets g^{z'_i}, \forall i \in S$
		C7Vec = tuple((ek_ID_A_S[i][1] * g ** zVec[i]) ** s for i, j in enumerate(S)) # $C_{7, i} \gets (\textit{ek}_{\textit{ID}_{A_{i, 2}}}(S) \cdot g^{z_i})^s, \forall i \in S$
		C8Vec = tuple(ek_ID_A_S[i][0] ** s * (H(uPrimeVec, ID_A) * TPrimeVec[j]) ** (s * zVec[i]) * H1( # $C_{8, i} \gets \textit{ek}_{\textit{ID}_{A_{i, 1}}}(S) \cdot [H(\bm{u}', \textit{ID}_A) T'_i]^{s \cdot z_i} \cdot H_1(
			self.__group.serialize(C) + self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) # C || C_{1, i} || C_{2, i} || C_{3, i}
			+ self.__group.serialize(C4Vec[i]) + self.__group.serialize(C5Vec[i]) + self.__group.serialize(C6Vec[i]) + self.__group.serialize(C7Vec[i]) # C_{4, i} || C_{5, i} || C_{6, i} || C_{7, i}
		) for i, j in enumerate(S)) # ), \forall i \in S$
		I = set(S).intersection(SPrimePrime) # $I \gets S \cap S''$
		if len(I) >= self.__d: # \textbf{if} $\|I\| \leqslant d$ \textbf{then}
			IStar = list(I)
			shuffle(IStar)
			IStar = tuple(sorted(IStar[:self.__d])) # \quad generate $I^* \subset I$ randomly
		else:
			IStar = list(I)
			I = list(set(range(self.__n)) - I)
			shuffle(I)
			while len(IStar) < self.__d:
				IStar.append(I.pop())
			IStar.sort()
			IStar = tuple(IStar)
		CT = (																				\
			SPrimePrime, IStar, C, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec, C6Vec, C7Vec, C8Vec	\
		) # $\textit{CT} \gets (S'', I^*, C, \vec{C}_1, \vec{C}_2, \vec{C}_3, \vec{C}_4, \vec{C}_5, \vec{C}_6, \vec{C}_7, \vec{C}_8)$
		
		# Return #
		return CT # \textbf{return} $\textit{CT}$
	def Dec(self:object, dkIDBSPrime:tuple, IDB:tuple, IDA:tuple, cipherText:tuple) -> Element|bool: # $\textbf{Dec}(\textit{dk}_{\textit{ID}_B}(S'), \textit{ID}_B, \textit{ID}_A, \textit{CT}) \rightarrow M$
		'''# Check #
		if not self.__flag:
			print("Dec: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if (																																								\
			isinstance(SA, tuple) and isinstance(PA, tuple) and isinstance(SB, tuple) and isinstance(PB, tuple) and len(SA) == len(PA) == len(SA) == len(SB) == self.__n	\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in SA) and all(isinstance(ele, Element) and ele.type == ZR for ele in PA)							\
			and all(isinstance(ele, Element) and ele.type == ZR for ele in SB) and all(isinstance(ele, Element) and ele.type == ZR for ele in PB)							\
		): # hybrid check
			ID_A, P_A, S_B, P_B = SA, PA, SB, PB
			if (																																							\
				isinstance(dkSBPA, tuple) and len(dkSBPA) == 2 and isinstance(dkSBPA[0], tuple) and isinstance(dkSBPA[1], tuple) and len(dkSBPA[0]) == len(dkSBPA[1]) == 5	\
				and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in dkSBPA[0]) and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in dkSBPA[1])	\
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
			print("Dec: The variable $\\textit{dk}_{S_B, P_A}$ has been generated accordingly. ")'''
		if isinstance(IDB, tuple) and len(IDB) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDB): # hybrid check
			ID_B = IDB
			if (																									\
				isinstance(dkIDBSPrime, tuple) and len(dkIDBSPrime) == self.__d and all(isinstance(ele[0], tuple)	\
				and isinstance(ele[1], tuple) and len(ele[0]) == len(ele[1]) == 2 for ele in dkIDBSPrime)			\
			): # hybrid check
				dk_ID_B_S_Prime = dkIDBSPrime
			else:
				dk_ID_B_S_Prime = self.DKGen(ID_B)
				print("Dec: The variable $\\textit{dk}_{\\textit{ID}_B}(S)'$ should be a tuple containing $d$ tuples but it is not, which has been generated accordingly. ")
		else:
			ID_B = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Dec: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
			dk_ID_B_S_Prime = self.DKGen(ID_B)
			print("Dec: The variable $\\textit{dk}_{\\textit{ID}_B}(S)'$ has been generated accordingly. ")
		if isinstance(IDA, tuple) and len(IDA) == self.__n and all(isinstance(ele, Element) and ele.type == ZR for ele in IDA): # hybrid check
			ID_A = IDA
		else:
			ID_A = tuple(self.__group.random(ZR) for _ in range(self.__n))
			print("Dec: The variable $\\textit{ID}_A$ should be a tuple containing $n$ elements of $\\mathbb{Z}_r$ but it is not, which has been generated randomly. ")
		if (																													\
			isinstance(cipherText, tuple) and len(cipherText) == 10 and all(isinstance(ele, Element) for ele in cipherText[:5])	\
			and all(isinstance(ele, tuple) and len(ele) == self.__n for ele in cipherText[5:])									\
		): # hybrid check
			CT = cipherText
		else:
			S = list(range(self.__n))
			shuffle(S)
			S = tuple(sorted(S[:self.__d]))
			CT = self.Enc(self.EKGen(ID_A, S), ID_A, ID_B, S, self.__group.random(GT))
			del S
			print("Dec: The variable $\\textit{CT}$ should be a tuple containing 5 elements and 5 tuples but it is not, which has been generated randomly. ")
		
		# Unpack #
		C, C1Vec, C2Vec, C3Vec, C4Vec, C5Vec, C6Vec, C7Vec = CT[2], CT[3], CT[4], CT[5], CT[6], CT[7], CT[8], CT[9]
		
		# Scheme #
		CTVec = tuple(																																								\
			self.__group.serialize(C) + self.__group.serialize(C1Vec[i]) + self.__group.serialize(C2Vec[i]) + self.__group.serialize(C3Vec[i]) + self.__group.serialize(C4Vec[i])	\
			+ self.__group.serialize(C5Vec[i]) + self.__group.serialize(C6Vec[i]) + self.__group.serialize(C7Vec[i]) for i in range(self.__n)										\
		) # $\textit{CT}_i \gets C || C_{1, i} || C_{2, i} || C_{3, i} || C_{4, i} || C_{5, i} || C_{6, i} || C{7, i}, \forall i \in \{1, 2, \cdots, n\}$
		KlPrime = self.__product(
			tuple((pair(C8Vec[i], g) / (pair(H(uPrimeVec, ID_A) * TPrime[i], C7Vec[i]) *pair(H1(CTVec[i]), C6Vec[i]))) ** Delta(i, I, 0) for i in IStar)
		) # $K'_l \gets \prod\limits_{i \in I^*} \left(\frac{e(C_{8, i}, g)}{e([H(\bm{u}', \textit{ID}_A) T'_i] e(H_1(\textit{CT}_i), C_{6, i})}\right)^{\Delta(i, I, 0)}$
		KsPrime = self.__product(																										\
			tuple((																														\
				(pair(C1Vec[i], dk_ID_B_SPrime[i][0]) * pair(C2Vec[i], dk_ID_B_SPrime[i][1]) * pair(C3Vec[i], dk_ID_B_SPrime[i][2]))	\
				/ (pair(C4Vec[i], dk_ID_B_SPrime[i][3]) * pair(C5Vec[i], dk_ID_B_SPrime[i][4]))											\
			) ** Delta(i, I, 0) for i in I)																								\
		) # $K'_s \gets \prod\limits_{i \in I} \left(\right)^{\Delta(i, j, 0)}$
		SPrimePrimeSet = set(SPrimePrime)
		if SPrimePrimeSet.intersection(S) >= self.__d and SPrimePrimeSet.intersection(SPrime) >= self.__d: # \textbf{if} $|S \cap S'| \leqslant d \land |S' \cap S''| \leqslant d$ \textbf{then}
			M = C * KsPrime * KlPrime # quad$M \gets C \cdot K'_s \cdot K'_l$
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


def conductScheme(curveType:tuple|list|str, n:int = 30, d:int = 10, run:int|None = None) -> list:
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
			if isinstance(run, int) and run >= 1:
				print("run =", run)
			print("Is the system valid? No. \n\t{0}".format(e))
			return (																																			\
				([curveType[0], curveType[1]] if (																												\
					isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int)			\
				) else [curveType if isinstance(curveType, str) else None, None])																				\
				+ [n if isinstance(n, int) else None, d if isinstance(d, int) else None, run if isinstance(run, int) else None] + [False] * 2 + [-1] * 13	\
			)
	else:
		print("Is the system valid? No. The parameter $n$ should be a positive integer, and the parameter $d$ should be a positive integer not smaller than $2$. ")
		return (																																							\
			([curveType[0], curveType[1]] if (																																\
				isinstance(curveType, (tuple, list)) and len(curveType) == 2 and isinstance(curveType[0], str) and isinstance(curveType[1], int)							\
			) else [curveType if isinstance(curveType, str) else None, None])																								\
			+ [n if isinstance(n, int) else None, d if isinstance(d, int) else None, run if isinstance(run, int) and run >= 1 else None] + [False] * 2 + [-1] * 13	\
		)
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	print("n =", n)
	print("d =", d)
	if isinstance(run, int) and run >= 1:
		print("run =", run)
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
	S = list(range(n))
	shuffle(S)
	S = tuple(sorted(S[:d]))
	ek_ID_A_S = schemeAAIBME.EKGen(ID_A, S)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# DKGen #
	startTime = perf_counter()
	ID_B = tuple(group.random(ZR) for _ in range(n))
	dk_ID_B_SPrime = schemeAAIBME.DKGen(ID_B)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Enc #
	startTime = perf_counter()
	message = group.random(GT)
	CT = schemeAAIBME.Enc(ek_ID_A_S, ID_A, ID_B, S, message)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# Dec #
	startTime = perf_counter()
	M = schemeAAIBME.Dec(dk_ID_B_SPrime, ID_B, ID_A, CT)
	endTime = perf_counter()
	timeRecords.append(endTime - startTime)
	
	# End #
	booleans = [True, not isinstance(M, bool) and message == M]
	spaceRecords = [																															\
		schemeAAIBME.getLengthOf(group.random(ZR)), schemeAAIBME.getLengthOf(group.random(G1)), schemeAAIBME.getLengthOf(group.random(GT)), 	\
		schemeAAIBME.getLengthOf(mpk), schemeAAIBME.getLengthOf(msk), schemeAAIBME.getLengthOf(ek_ID_A_S), 										\
		schemeAAIBME.getLengthOf(dk_ID_B_SPrime), schemeAAIBME.getLengthOf(CT)																	\
	]
	del schemeAAIBME
	print("Original:", message)
	print("Decrypted:", M)
	print("Is the scheme correct (message == M)? {0}. ".format("Yes" if booleans[1] else "No"))
	print("Time:", timeRecords)
	print("Space:", spaceRecords)
	print()
	return [group.groupType(), group.secparam, n, d, run if isinstance(run, int) else None] + booleans + timeRecords + spaceRecords

def main() -> int:
	parser = Parser(argv)
	flag, encoding, outputFilePath, roundCount, waitingTime, overwritingConfirmed = parser.parse()
	if flag > EXIT_SUCCESS and flag > EOF:
		outputFilePath, overwritingConfirmed = parser.checkOverwriting(outputFilePath, overwritingConfirmed)
		del parser
		
		# Parameters #
		curveTypes = (("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))
		queries = ("curveType", "secparam", "n", "d", "roundCount")
		validators = ("isSystemValid", "isSchemeCorrect")
		metrics = (																	\
			"Setup (s)", "EKGen (s)", "DKGen (s)", "Enc (s)", "Dec (s)", 			\
			"elementOfZR (B)", "elementOfG1G2 (B)", "elementOfGT (B)", 				\
			"mpk (B)", "msk (B)", "ek_ID_A_S (B)", "dk_ID_B_SPrime (B)", "CT (B)"	\
		)
		
		# Scheme #
		columns, qLength, results = queries + validators + metrics, len(queries), []
		length, qvLength, avgIndex = len(columns), qLength + len(validators), qLength - 1
		saver = Saver(outputFilePath, columns)
		if saver.initialize():
			try:
				for curveType in curveTypes:
					for n in range(10, 31, 5):
						for d in range(5, n, 5):
							averages = conductScheme(curveType, n = n, d = d, run = 1)
							for run in range(2, roundCount + 1):
								result = conductScheme(curveType, n = n, d = d, run = run)
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