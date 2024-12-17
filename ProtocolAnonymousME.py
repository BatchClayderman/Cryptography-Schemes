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
	from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element
except:
	print("The environment of the ``charm`` library is not handled correctly. ")
	print("See https://blog.csdn.net/weixin_45726033/article/details/144254189 if necessary. ")
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


class ProtocolAnonymousME:
	def __init__(self, group:None|PairingGroup = None) -> None:
		self.__group = group if isinstance(group, PairingGroup) else PairingGroup("SS512", secparam = 512)
		self.__l = 30
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
	def Setup(self:object, l:int = 30) -> tuple: # Setup(l) -> (mpk, msk)
		# Check #
		self.__flag = False
		if isinstance(l, int) and l >= 3: # $l$ must be not smaller than $3$ to complete all the tasks
			self.__l = l
		else:
			self.__l = 30
			print("The variable $l$ must be not smaller than $3$ to complete all the tasks. It has been defaulted to $30$. ")
		
		# Protocol #
		g = self.__group.random(G1) # generate $g \in \mathbb{G}_1$ randomly
		alpha, b1, b2 = self.__group.random(ZR), self.__group.random(ZR), self.__group.random(ZR) # generate $\alpha, b_1, b_2, \in \mathbb{Z}_p^*$ randomly
		g2, g3 = self.__group.random(G2), self.__group.random(G2) # generate $g_2, g_3 \in \mathbb{G}_2$ randomly
		h = tuple(self.__group.random(G2) for _ in range(self.__l)) # generate $h_1, h_2, \cdots, h_l \in \mathbb{G}_2$ randomly (Note that the indexes in implementations are 1 smaller than those in theory)
		g1 = g ** alpha # $g_1 \gets g^\alpha$
		gBar = g ** b1 # $\bar{g} \gets g^{b_1}$
		gTilde = g ** b2 # $\tilde{g} \gets g^{b_2}$
		g3Bar = g3 ** (1 / b1) # $\bar{g}_3 \gets g_3^{\cfrac{1}{b_1}}$
		g3Tilde = g3 ** (1 / b2) # $\tilde{g}_3 \gets g_3^{\cfrac{1}{b_2}}$
		self.__mpk = (g, g1, g2, g3, gBar, gTilde, g3Bar, g3Tilde) + h # $\textit{mpk} \gets (g, g_1, g_2, g_3, \bar{g}, \tilde{g}, \bar{g}_3, \tilde{g}_3, h_1, h_2, \cdots, h_l)$
		self.__msk = (g2 ** alpha, b1, b2) # $\textit{msk} \gets (g_2^\alpha, b_1, b_2)$
		
		# Flag #
		self.__flag = True
		return (self.__mpk, self.__msk)
	def KGen(self:object, IDk:tuple) -> tuple: # KGen(ID_k) -> sk_ID_k
		# Check #
		if not self.__flag:
			print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``KGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l: # boundary check
			ID_k = IDk
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print("The variable $\\textit{{ID}}_k$ should be a tuple whose length $k = \\|\\textit{{ID}}_k\\|$ is an integer within the closed interval $[2, {0}]$. It has been generated randomly with a length of ${1} - 1 = {0}$. ".format(self.__l - 1, self.__l))
		
		# Unpack #
		g, g3Bar, g3Tilde, h = self.__mpk[0], self.__mpk[6], self.__mpk[7], self.__mpk[8:]
		g2ToThePowerOfAlpha, b1, b2 = self.__msk
		k = len(ID_k)
		
		# Protocol #
		r = self.__group.random(ZR) # generate $r \in \mathbb{Z}_p^*$ randomly
		HI = self.__product(tuple(h[i] ** ID_k[i] for i in range(k))) # $\textit{HI} \gets h_1^{I_1}h_2^{I_2}\cdots h_k^{I_k}$
		sk_ID_k = ( # $\textit{sk}_\textit{ID}_k \gets (
			(
				g2ToThePowerOfAlpha ** (b1 ** (-1)) * HI ** (r / b1) * g3Bar ** r, # g_2^{\cfrac{\alpha}{b_1}} \cdot \textit{HI}^{\cfrac{r}{b_1}} \cdot \bar{g}_3^r, 
				g2ToThePowerOfAlpha ** (b2 ** (-1)) * HI ** (r / b2) * g3Tilde ** r, # g_2^{\cfrac{\alpha}{b_2}} \cdot \textit{HI}^{\cfrac{r}{b_2}} \cdot \tilde{g}_3^r, 
				g ** r # g^r, 
			)
			+ tuple(h[i] ** (r / b1) for i in range(k, self.__l)) # h_{k + 1}^{\cfrac{r}{b_1}}, h_{k + 2}^{\cfrac{r}{b_1}}, \cdots, h_l^{\cfrac{r}{b_1}}, 
			+ tuple(h[i] ** (r / b2) for i in range(k, self.__l)) # h_{k + 1}^{\cfrac{r}{b_2}}, h_{k + 2}^{\cfrac{r}{b_1}}, \cdots, h_l^{\cfrac{r}{b_1}}, 
			+ tuple(h[i] ** (b1 ** (-1)) for i in range(k, self.__l)) # h_{k + 1}^{b_1^{-1}}, h_{k + 2}^{b_1^{-1}}, \cdots, h_l^{b_1^{-1}}, 
			+ tuple(h[i] ** (b2 ** (-1)) for i in range(k, self.__l)) # h_{k + 1}^{b_2^{-1}}, h_{k + 2}^{b_2^{-1}}, \cdots, h_l^{b_2^{-1}}, 
			+ (HI ** (b1 ** (-1)), HI ** (b2 ** (-1))) # \textit{HI}^{b_1^{-1}}, \textit{HI}^{b_2^{-1}}
		) # )$
		
		# Return #
		return sk_ID_k
	def DerivedKGen(self:object, skIDkMinus1:tuple, IDk:tuple) -> tuple: # DerivedKGen(sk_ID_kMinus1, ID_k) -> sk_ID_k
		# Check #
		if not self.__flag:
			print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``DerivedKGen`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l: # boundary check
			ID_k = IDk
			if isinstance(skIDkMinus1, tuple) and len(skIDkMinus1) == ((self.__l - len(IDk) + 1) << 2) + 5: # check the length of $\textit{sk}_\textit{ID}_k$
				sk_ID_kMinus1 = skIDkMinus1
			else:
				sk_ID_kMinus1 = self.KGen(ID_k[:-1])
				print("The variable $\\textit{sk}_\\textit{ID}_{k - 1}$ is invalid, which has been computed again. ")
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print("The variable $\\textit{{ID}}_k$ should be a tuple whose length $k = \\|\\textit{{ID}}_k\\|$ is an integer within the closed interval $[2, {0}]$. It has been generated randomly with a length of ${1} - 1 = {0}$. ".format(self.__l - 1, self.__l))
			sk_ID_kMinus1 = self.KGen(ID_k[:-1])
			print("The variable $\\textit{sk}_\\textit{ID}_{k - 1}$ is generated correspondingly. ")
		
		# Unpack #
		g, g3Bar, g3Tilde, h = self.__mpk[0], self.__mpk[6], self.__mpk[7], self.__mpk[8:]
		k = len(ID_k)
		a0, a1, b, f0, f1 = sk_ID_kMinus1[0], sk_ID_kMinus1[1], sk_ID_kMinus1[2], sk_ID_kMinus1[-2], sk_ID_kMinus1[-1] # first 3 and last 2
		lengthPerToken = self.__l - k + 1
		c0, c1, d0, d1 = sk_ID_kMinus1[3:3 + lengthPerToken], sk_ID_kMinus1[3 + lengthPerToken:3 + (lengthPerToken << 1)], sk_ID_kMinus1[-2 - (lengthPerToken << 1):-2 - lengthPerToken], sk_ID_kMinus1[-2 - lengthPerToken:-2]
		
		# Protocol #
		t = self.__group.random(ZR) # generate $t \in \mathbb{Z}_p^*$ randomly
		sk_ID_k = ( # $\textit{sk}_\textit{ID}_k \gets (
			(
				a0 * c0[0] ** ID_k[k - 1] * (f0 * d0[0] ** ID_k[k - 1] * g3Bar) ** t, # a_0 \cdot c_{0, k}^{I_k} \cdot (f_0 \cdot d_{0, k}^{I_k} \cdot \bar{g}_3)^t, 
				a1 * c1[0] ** ID_k[k - 1] * (f1 * d1[0] ** ID_k[k - 1] * g3Tilde) ** t, # a_1 \cdot c_{1, k}^{I_k} \cdot (f_1 \cdot d_{1, k}^{I_k} \cdot \tilde{g}_3)^t, 
				b * g ** t, # b \cdot g^t, 
			)
			+ tuple(c0[i] * d0[i] ** t for i in range(1, lengthPerToken)) # c_{0, k + 1} \cdot d_{0, k + 1}^t, c_{0, k + 2} \cdot d_{0, k + 2}^t, \cdots, c_{0, l} \cdot d_{0, l}^t, 
			+ tuple(c1[i] * d1[i] ** t for i in range(1, lengthPerToken)) # c_{1, k + 1} \cdot d_{1, k + 1}^t, c_{1, k + 2} \cdot d_{1, k + 2}^t, \cdots, c_{1, l} \cdot d_{1, l}^t, 
			+ tuple(d0[i] for i in range(1, lengthPerToken)) # d_{0, k + 1}, d_{0, k + 2}, \cdots, d_{0, l}, 
			+ tuple(d1[i] for i in range(1, lengthPerToken)) # d_{1, k + 1}, d_{1, k + 2}, \cdots, d_{1, l}, 
			+ (f0 * c0[0] ** ID_k[k - 1], f1 * c1[0] ** ID_k[k - 1]) # f_0 \cdot c_{0, k}^I_k, f_1 \cdot c_{1, k}^I_k
		) # )$
		
		# Return #
		return sk_ID_k
	def Enc(self:object, IDk:tuple, message:Element) -> object: # Enc(ID_k, M) -> CT
		# Check #
		if not self.__flag:
			print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Enc`` subsequently. ")
			self.Setup()
		if isinstance(IDk, tuple) and 2 <= len(IDk) < self.__l: # boundary check
			ID_k = IDk
		else:
			ID_k = tuple(self.__group.random(ZR) for i in range(self.__l - 1))
			print("The variable $\\textit{{ID}}_k$ should be a tuple whose length $k = \\|\\textit{{ID}}_k\\|$ is an integer within the closed interval $[2, {0}]$. It has been generated randomly with a length of ${1} - 1 = {0}$. ".format(self.__l - 1, self.__l))
		if isinstance(message, Element):
			M = message
		else:
			M = self.__group.random(GT)
			print("The message passed should be a $\\mathbb{G}_T$ element but it is not. It will be generated randomly. ")
		
		# Unpack #
		g1, g2, g3, gBar, gTilde, h = self.__mpk[1], self.__mpk[2], self.__mpk[3], self.__mpk[4], self.__mpk[5], self.__mpk[8:]
		k = len(ID_k)
		
		# Protocol #
		s1, s2 = self.__group.random(ZR), self.__group.random(ZR) # generate $s_1, s_2 \in \mathbb{Z}_p^*$ randomly
		CT = ( # $\textit{CT} \gets (
			pair(g1, g2) ** (s1 + s2) * M, # e(g_1, g_2)^{s_1 + s_2} \cdot M, 
			gBar ** s1, # \bar{g}^{s_1}, 
			gTilde ** s2, # \tilde{g}^{s_2}, 
			(g3 * self.__product(tuple(h[i] ** ID_k[i] for i in range(k)))) ** (s1 + s2) # (h_1^{I_1}h_2^{I_2} \cdots h_k^{I_k} \cdot g_3)^{s_1 + s_2}
		) # )$
		
		# Return #
		return CT
	def Dec(self:object, cipher:tuple, skIDk:tuple) -> bytes: # Dec(CT, sk_ID_k) -> M
		# Check #
		if not self.__flag:
			print("The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``Dec`` subsequently. ")
			self.Setup()
		if isinstance(skIDk, tuple) and 9 <= len(skIDk) <= 5 + ((self.__l - 1) << 2): # boundary check
			sk_ID_k = skIDk
			if isinstance(cipher, tuple) and 4 == len(cipher):
				CT = cipher
			else:
				CT = self.Enc(tuple(self.__group.random(ZR) for i in range(self.__l - 1)), self.__group.random(GT))
				print("The variable $\\textit{CT}$ is invalid, which has been computed again with $M \\in \\mathbb{G}_T$ generated randomly. ")
		else:
			sk_ID_k = self.KGen(tuple(self.__group.random(ZR) for i in range(self.__l - 1)))
			print("The variable $\\textit{{ID}}_k$ should be a tuple whose length $k = \\|\\textit{{ID}}_k\\|$ is an integer within the closed interval $[9, {0}]$. It has been generated randomly with a length of $9$. ".format(5 + ((self.__l - 1) << 2)))
			CT = self.Enc(tuple(self.__group.random(ZR) for i in range(self.__l - 1)), self.__group.random(GT))
			print("The variable $\\textit{CT}$ has been generated accordingly. ")
		
		# Unpack #
		A, B, C, D = CT
		a0, a1, b = sk_ID_k[0], sk_ID_k[1], sk_ID_k[2]
		
		# Protocol #
		M = pair(b, D) * A / (pair(B, a0) * pair(C, a1)) # $M \gets \cfrac{e(b, D) \cdot A}{e(B, a_0) \cdot e(C, a_1)}$
		
		# Return #
		return M


def Protocol(curveType:str, k:int, l:int) -> list:
	# Begin #
	if isinstance(k, int) and isinstance(l, int) and 2 <= k < l:
		try:
			group = PairingGroup(curveType)
		except:
			print("Is the system valid? No")
			return [curveType, l, k, False, False, False] + [-1] * 13
	else:
		print("Is system valid? No")
		return [curveType, l, k, False, False, False] + [-1] * 13
	process = Process(os.getpid())
	print("Type =", curveType)
	print("l =", l)
	print("k =", k)
	print("Is the system valid? Yes")
	
	# Initialization #
	protocolAnonymousME = ProtocolAnonymousME(group)
	timeRecords, memoryRecords = [], []
	
	# Setup #
	startTime = time()
	mpk, msk = protocolAnonymousME.Setup(l)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# KGen #
	startTime = time()
	ID_k = tuple(group.random(ZR) for i in range(k))
	sk_ID_k = protocolAnonymousME.KGen(ID_k)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# DerivedKGen #
	startTime = time()
	sk_ID_kMinus1 = protocolAnonymousME.KGen(ID_k[:-1]) # remove the last one to generate the sk_ID_kMinus1
	sk_ID_kDerived = protocolAnonymousME.DerivedKGen(sk_ID_kMinus1, ID_k)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Enc #
	startTime = time()
	message = group.random(GT)
	CT = protocolAnonymousME.Enc(ID_k, message)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# Dec #
	startTime = time()
	M = protocolAnonymousME.Dec(CT, sk_ID_k)
	MDerived = protocolAnonymousME.Dec(CT, sk_ID_kDerived)
	endTime = time()
	timeRecords.append(endTime - startTime)
	memoryRecords.append(process.memory_info().rss)
	
	# End #
	sizeRecords = [getsizeof(sk_ID_k), getsizeof(sk_ID_kDerived), getsizeof(CT)]
	del protocolAnonymousME
	print("Is the derver passed (message == M')? {0}".format("Yes" if message == MDerived else "No"))
	print("Is the protocol correct (message == M)? {0}".format("Yes" if message == M else "No"))
	print("Time:", timeRecords)
	print("Memory:", memoryRecords)
	print("Size:", sizeRecords)
	print()
	return [curveType, l, k, True, message == MDerived, message == M] + timeRecords + memoryRecords + sizeRecords

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
	results, filePath = [], "ProtocolAnonymousME.xlsx"
	for curveType in ("MNT159", "MNT201", "MNT224"):
		for l in (5, 10, 15, 20, 25, 30):
			for k in range(5, l, 5):
				results.append(Protocol(curveType, k, l))
	if results:
		columns = ["Curve", "l", "k", "isSystemValid", "isDeriverPassed", "isProtocolCorrect", "Setup (s)", "KGen (s)", "DerivedKGen (s)", "Enc (s)", "Dec (s)", "Setup (B)", "KGen (B)", "DerivedKGen (B)", "Enc (B)", "Dec (B)", "SK (B)", "SK' (B)", "CT"]
		if handleFolder(os.path.split(filePath)[0]):
			try:
				df = __import__("pandas").DataFrame(results, columns = columns)
				if os.path.splitext(filePath)[1].lower() == ".csv":
					df.to_csv(filePath, index = False)
				else:
					df.to_excel(filePath, index = False)
				print("\nSuccessfully saved the results to \"{0}\" in the three-line table form. ".format(filePath))
			except BaseException as e:
				print("\nFailed to save the results to \"{0}\" in the three-line table form since {1}. \nThe Program will try to use the plain text form. ".format(filePath, e))
				try:
					with open(filePath, "w", encoding = "utf-8") as f:
						f.write(str(columns) + "\n" + str(results))
					print("\nSuccessfully saved the results to \"{0}\" in the plain text form. ".format(filePath))
				except BaseException as ee:
					print("\nResults: \n{0}\n\nFailed to save the results to \"{1}\" since {2}. \nPlease press the enter key to exit ({3}). ".format(results, filePath, ee, EOF))
					input()
					return EOF
		else:
			print("\nResults: \n{0}\n\nFailed to save the results to \"{1}\" since the parent folder was not created successfully. \nPlease press the enter key to exit ({0}). ".format(results, filePath, EOF))
			input()
			return EOF
	else:
		print("The results are empty. Please press the enter key to exit ({0}). ".format(EOF))
		input()
		return EOF
	iRet = EXIT_SUCCESS if all([all(result[3:6]) for result in results]) else EXIT_FAILURE
	print("Please press the enter key to exit ({0}). ".format(iRet))
	input()
	return iRet



if "__main__" == __name__:
	exit(main())