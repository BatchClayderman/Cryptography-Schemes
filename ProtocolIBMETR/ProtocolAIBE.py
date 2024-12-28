import os
from sys import exit, getsizeof
from time import time
try:
	from psutil import Process
except:
	print("Cannot compute the memory via ``psutil.Process``. ")
	print("Please try to install psutil via ``python -m pip install psutil`` or ``apt-get install python3-psutil``. ")
	print("Please press the enter key to exit. ")
	input()
	exit(-1)
try:
	from charm.toolbox.pairinggroup import PairingGroup, G1, GT, ZR, pair, pc_element as Element
except:
	print("The environment of the ``charm`` library is not handled correctly. ")
	print("See https://blog.csdn.net/weixin_45726033/article/details/144254189 in Chinese sif necessary. ")
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


class ProtocolAIBE:
	def __init__(self:object, group:None|PairingGroup = None) -> None:
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		if self.__group.secparam < 1:
			self.__group = PairingGroup(self.__group.groupType())
			print("Init: The securtiy parameter should be a positive integer but it is not, which has been defaulted to {0}. ".format(self.__group.secparam))
		self.__mpk = None
		self.__msk = None
		self.__flag = False # to indicate whether it has already set up
	def Setup(self:object) -> tuple: # $\textbf{Setup}(l) \rightarrow (\textit{mpk}, \textit{msk})$
		# Check #
		self.__flag = False
		
		# Protocol #
		g, g0, g1 = self.__group.random(G1), self.__group.random(G1), self.__group.random(G1) # generate $g, g_0, g_1 \in \mathbb{G}_1$ randomly
		w, t1, t2, t3, t4 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $w, t_1, t_2, t_3, t_4 \in \mathbb{Z}_p^*$
		Omega = pair(g, g) ** (t1 * t2 * w) # $\Omega \gets e(g, g)^{t_1 t_2 w}$
		v1 = g ** t1 # $v \gets g^{t_1}$
		v2 = g ** t2 # $v \gets g^{t_2}$
		v3 = g ** t3 # $v \gets g^{t_3}$
		v4 = g ** t4 # $v \gets g^{t_4}$
		self.__mpk = (Omega, g, g0, g1, v1, v2, v3, v4) # $\textit{mpk} \gets (Omega, g, g_0, g_1, v_1, v_2, v_3, v_4)$
		self.__msk = (w, t1, t2, t3, t4) # $\textit{msk} \gets (w, t_1, t_2, t_3, t_4)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk) # $\textbf{return }(\textit{mpk}, \textit{msk})$
	def Extract(self:object, identity:Element) -> Element: # $\textbf{Extract}(\textit{Id}) \rightarrow \textit{Pvk}_\textit{Id}$
		# Check #
		if not self.__flag:
			print("Extract: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Extract`` subsequently. ")
			self.Setup()
		if isinstance(identity, Element) and identity.type == ZR: # type check
			Id = identity
		else:
			Id = self.__group.random(ZR)
			print("Extract: The variable $\\textit{Id}$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		g, g0, g1 = self.__mpk[1], self.__mpk[2], self.__mpk[3]
		w, t1, t2, t3, t4 = self.__msk
		
		# Protocol #
		r1, r2 = self.__group.random(ZR), self.__group.random(ZR) # generate $r1, r2 \in \mathbb{Z}_p^*$ randomly
		d0 = g ** (r1 * t1 * t2 + r2 * t3 * t4) # $d_0 \gets g^{r_1 t_1 t_2 + r_2 t_3 t_4}$
		d1 = g ** (-(w * t2)) * (g0 * g1 ** Id) ** (-(r1 * t2)) # $d_1 \gets g^{- w t_2} \cdot (g_0 g_1^\textit{Id})^{-  r_1 t_2}$
		d2 = g ** (-(w * t1)) * (g0 * g1 ** Id) ** (-(r1 * t1)) # $d_2 \gets g^{- w t_1} \cdot (g_0 g_1^\textit{Id})^{-  r_1 t_1}$
		d3 = (g0 * g1 ** Id) ** (-(r2 * t4)) # $d_3 \gets (g_0 g_1^\textit{Id})^{-  r_2 t_4}$
		d4 = (g0 * g1 ** Id) ** (-(r2 * t3)) # $d_4 \gets (g_0 g_1^\textit{Id})^{-  r_2 t_3}$
		Pvk_Id = (d0, d1, d2, d3, d4) # $\textit{Pvk}_\textit{Id} \gets (d_0, d_1, d_2, d_3, d_4)$
		
		# Return #
		return Pvk_Id # $\textbf{return }\textit{Pvk}_\textit{Id}$
	def Encrypt(self:object, identity:Element, message:Element) -> Element: # $\textbf{Encrypt}(\textit{Id}, m) \rightarrow \textit{CT}$
		# Check #
		if not self.__flag:
			print("Encrypt: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Encrypt`` subsequently. ")
			self.Setup()
		if isinstance(identity, Element) and identity.type == ZR: # type check
			Id = identity
		else:
			Id = self.__group.random(ZR)
			print("Encrypt: The variable $\\textit{Id}$ should be an element of $\\mathbb{Z}_p^*$ but it is not, which has been generated randomly. ")
		if isinstance(message, Element) and message.type == GT: # type check
			M = message
		else:
			M = self.__group.random(GT)
			print("Encrypt: The variable $M$ should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ")
		
		# Unpack #
		Omega, g0, g1, v1, v2, v3, v4 = self.__mpk[0], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[6], self.__mpk[7]
		
		# Protocol #
		s, s1, s2 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $s, s_1, s_2 \in \mathbb{Z}_p^*$ randomly
		CPi = Omega ** s * M # $C' \gets \Omega^s M$
		C0 = (g0 * g1 ** Id) ** s # $(g_0 g_1^\textit{Id})^s$
		C1 = v1 ** (s - s1) # $C_1 \gets v_1^{s - s_1}$
		C2 = v2 ** s1 # $C_2 \gets v_2^{s_1}$
		C3 = v3 ** (s - s2) # $C_3 \gets v_3^{s - s_2}$
		C4 = v4 ** s2 # $C_4 \gets v_4^{s_2}$
		CT = (CPi, C0, C1, C2, C3, C4) # $\textit{CT} \gets (C', C_0, C_1, C_2, C_3, C_4)$
		
		# Return #
		return CT # $\textbf{return }\textit{CT}$
	def Decrypt(self:object, PvkId:tuple, cipher:tuple) -> bytes: # $\textbf{Dec}(\textit{Pvk}_\textit{id}, \textit{CT}) \rightarrow M$
		# Check #
		if not self.__flag:
			print("Decrypt: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Decrypt`` subsequently. ")
			self.Setup()
		if isinstance(PvkId, tuple) and len(PvkId) == 5 and all([isinstance(ele, Element) for ele in PvkId]): # hybrid check
			Pvk_Id = PvkId
		else:
			Pvk_Id = self.Extract(self.__group.random(ZR))
			print("Decrypt: The variable $\\textit{Pvk}_\\textit{Id}$ should be a tuple containing 5 elements but it is not, which has been generated randomly. ")
		if isinstance(cipher, tuple) and len(cipher) == 6 and all([isinstance(ele, Element) for ele in cipher]): # hybrid check
			CT = cipher
		else:
			CT = self.Encrypt(self.__group.random(ZR), self.__group.random(ZR))
			print("Decrypt: The variable $\\textit{CT}$ should be a tuple containing 6 elements but it is not, which has been generated randomly. ")
		
		# Unpack #
		d0, d1, d2, d3, d4 = Pvk_Id
		CPi, C0, C1, C2, C3, C4 = CT
		
		# Protocol #
		M = CPi * pair(C0, d0) * pair(C1, d1) * pair(C2, d2) * pair(C3, d3) * pair(C4, d4) # $M \gets C' \cdot e(C_0, d_0) \cdot e(C_1, d_1) \cdot e(C_2, d_2) \cdot e(C_3, d_3) \cdot e(C_4, d_4)$
		
		# Return #
		return M # $\textbf{return }M$


def Protocol(curveType:tuple|list|str, round:int = None) -> list:
	# Begin #
	try:
		group = PairingGroup(curveType[0], secparam = curveType[1]) if isinstance(curveType, (tuple, list)) and len(curveType) == 2 else PairingGroup(curveType)
	except:
		if isinstance(curveType, (tuple, list)):
			if len(curveType) == 2:
				print("curveType =", curveType[0])
				print("secparam =", curveType[1])
			else:
				print("curveType =", curveType)
		elif isinstance(curveType, str):
			print("curveType =", curveType)
		print("Is the system valid? No. {0}. ".format(e))
		return ([curveType[0], curveType[1]] if isinstance(curveType, (tuple, list)) and len(curveType) == 2 else [curveType, None]) + [False] * 2 + [-1] * 10
	process = Process(os.getpid())
	print("curveType =", group.groupType())
	print("secparam =", group.secparam)
	if isinstance(round, int):
		print("Round =", round)
	print("Is the system valid? Yes. ")
	
	# Initialization #
	protocolAIBE = ProtocolAIBE(group)
	timeRecords, memoryRecords = [], []
	
	# Setup #
	startTime = time()
	mpk, msk = protocolAIBE.Setup()
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Extract #
	startTime = time()
	Id = group.random(ZR)
	Pvk_Id = protocolAIBE.Extract(Id)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Encrypt #
	startTime = time()
	message = group.random(GT)
	CT = protocolAIBE.Encrypt(Id, message)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Decrypt #
	startTime = time()
	M = protocolAIBE.Decrypt(Pvk_Id, CT)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# End #
	sizeRecords = [getsizeof(Pvk_Id), getsizeof(CT)]
	del protocolAIBE
	print("Is the protocol correct (message == M)? {0}. ".format("Yes" if message == M else "No"))
	print("Time:", timeRecords)
	print("Memory:", memoryRecords)
	print("Size:", sizeRecords)
	print()
	return [group.groupType(), group.secparam, True, message == M] + timeRecords + memoryRecords + sizeRecords

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
	roundCount, filePath = 20, "ProtocolAIBE.xlsx"
	columns = [																								\
		"curveType", "secparam", "isSystemValid", "isProtocolCorrect", "Setup (s)", "Extract (s)", "Encrypt (s)", "Decrypt (s)", 	\
		"Setup (B)", "Extract (B)", "Encrypt (B)", "Decrypt (B)", "Pvk_Id (B)", "CT (B)"									\
	]
	
	# Protocol #
	length, results = len(columns), []
	try:
		for curveType in curveTypes:
			rounds = []
			for round in range(roundCount):
				rounds.append(Protocol(curveType, round))
			if rounds:
				average = [rounds[0][0], rounds[0][1]]
				for idx in range(2, 4):
					average.append("{0}/{1}".format([round[idx] for round in rounds].count(True), roundCount))
				for idx in range(4, length):
					values = [round[idx] for round in rounds]
					average.append(-1 if -1 in values else sum(values) / roundCount)
				results.append(average)
	except KeyboardInterrupt:
		print("The experiments were interrupted by users. The program will try to save the results collected. ")
	except BaseException as e:
		print("The experiments were interrupted by the following exceptions. The program will try to save the results collected. ")
		print(e)
	
	# Output #
	if results:
		if handleFolder(os.path.split(filePath)[0]):
			try:
				df = __import__("pandas").DataFrame(results, columns = columns)
				if os.path.splitext(filePath)[1].lower() == ".csv":
					df.to_csv(filePath, index = False)
				else:
					df.to_excel(filePath, index = False)
				print("\nSuccessfully saved the results to \"{0}\" in the three-line table form. ".format(filePath))
			except:
				try:
					with open(filePath, "w", encoding = "utf-8") as f:
						f.write(str(columns) + "\n" + str(results))
					print("\nSuccessfully saved the results to \"{0}\" in the plain text form. ".format(filePath))
				except BaseException as e:
					print("\nResults: \n{0}\n\nFailed to save the results to \"{1}\" since {2}. ".format(results, filePath, e))
		else:
			print("\nResults: \n{0}\n\nFailed to save the results to \"{1}\" since the parent folder was not created successfully. ".format(results, filePath))
	else:
		print("The results are empty. ")
	
	# End #
	iRet = EXIT_SUCCESS if results else EXIT_FAILURE
	print("Please press the enter key to exit ({0}). ".format(iRet))
	input()
	return iRet



if "__main__" == __name__:
	exit(main())