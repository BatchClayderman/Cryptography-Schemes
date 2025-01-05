import os
from sys import argv, executable, exit
from re import findall
from subprocess import Popen
from time import sleep, time
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)
STARTUP_COMMAND_FORMAT = "START \"\" \"{0}\" \"{1}\" \"{2}\"" if __import__("platform").system().upper() == "WINDOWS" else "\"{0}\" \"{1}\" \"{2}\" &"


def getTxt(filePath:str, index:int = 0) -> str: # get .txt content
	coding = ("utf-8", "gbk", "utf-16") # codings
	if 0 <= index < len(coding): # in the range
		try:
			with open(filePath, "r", encoding = coding[index]) as f:
				content = f.read()
			return content[1:] if content.startswith("\ufeff") else content # if utf-8 with BOM, remove BOM
		except (UnicodeError, UnicodeDecodeError):
			return getTxt(filePath, index + 1) # recursion
		except:
			return None
	else:
		return None # out of range

def fetchPrompts(filePath:str, idx:int, functionName:str, s:str, sleepingTime:int = 5) -> bool|None:
	if isinstance(filePath, str) and isinstance(idx, int) and isinstance(functionName, str) and isinstance(s, str):
		if s in (
			"Cannot compute the memory via ``psutil.Process``. ", 
			"Please try to install psutil via ``python -m pip install psutil`` or ``apt-get install python3-psutil``. ", 
			"Please press the enter key to exit. ", 
			"The environment of the ``charm`` library is not handled correctly. ", 
			"See https://blog.csdn.net/weixin_45726033/article/details/144254189 if necessary. ", 
			"Setup: The variable $l$ should be an integer not smaller than $3$ but it is not, which has been defaulted to $30$. ", 
			functionName + ": The message passed should be an element of $\\mathbb{G}_T$ but it is not, which has been generated randomly. ", 
			"{0}: The ``Setup`` procedure has not been called yet. The program will call the ``Setup`` first and finish the ``{0}`` subsequently. ".format(functionName), 
		):
			return True
		elif findall("^{0}: The variable \\$.+\\$ should be an element of \\$\\\\\\\\mathbb\\{{Z\\}}_p\\^\\*\\$ but it is not, which has been generated randomly. $".format(functionName), s):
			return True
		elif findall("^{0}: The variable \\$.+\\$ is generated correspondingly. $".format(functionName), s):
			return True
		else:
			print("\"{0}\" ({1}): \"{2}\" (in Function ``{3}``)".format(filePath, idx, s.replace("\\", "\\\\").replace("\"", "\\\""), functionName))
			try:
				sleep(sleepingTime)
			except:
				pass
			return False
	else:
		return None

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

def generateSchemeTxt(pythonFilePath:str) -> bool:
	if isinstance(pythonFilePath, str):
		if os.path.splitext(pythonFilePath)[1].lower() == ".py":
			content, folderPath, fileName = getTxt(pythonFilePath), pythonFilePath[:-3] + "LaTeX", os.path.split(pythonFilePath)[1][:-3] + ".tex"
			if content is None:
				print("Failed to read \"{0}\". ".format(pythonFilePath))
				return False
			elif handleFolder(folderPath):
				# LaTeX Generation #
				try:
					startTime = time()
					with open(os.path.join(folderPath, fileName), "w", encoding = "utf-8") as f:
						f.write("\\documentclass[a4paper]{article}\n\\setlength{\\parindent}{0pt}\n\\usepackage{amsmath,amssymb}\n\\usepackage{bm}\n\n\\begin{document}\n\n\\section{Scheme}\n\n")
						classFlag, functionFlag, schemeFlag, doubleSeparatorFlag, printFlag, buffer = False, None, False, True, False, ""
						for idx, line in enumerate(content.splitlines()):
							if line.startswith("class Scheme"):
								classFlag = True
							elif classFlag and line.startswith("\tdef ") and "(self:object" in line and "): # " in line:
								f.write("\\subsection{" + line[line.index("): # ") + 5:].strip() + "}\n\n")
								functionFlag = line[5:line.index("(self:object")]
							elif classFlag and functionFlag and "\t\t# Scheme #" == line:
								schemeFlag = True
							elif classFlag and functionFlag and schemeFlag and line.count("#") == 1 and "#" in line:
								prompt = line[line.index("#") + 1:].strip()
								if "$" == prompt:
									doubleSeparatorFlag = not doubleSeparatorFlag # invert the double separator switch
								elif prompt.startswith("$") and not prompt.endswith("$"):
									doubleSeparatorFlag = False # disable the double separator switch
								elif not prompt.startswith("$") and prompt.endswith("$"):
									doubleSeparatorFlag = True # enable the double separator switch
								f.write(prompt + ("\n\n" if doubleSeparatorFlag else "\n"))
							elif line.strip() and not line.startswith("\t") and not line.lstrip().startswith("#"):
								classFlag, functionFlag, schemeFlag, doubleSeparatorFlag = False, False, False, True # reset
							if functionFlag and schemeFlag and line.startswith("\t\treturn "):
								functionFlag, schemeFlag = False, False
							if "print(\"" in line and "\")" in line:
								fetchPrompts(pythonFilePath, idx, functionFlag, line[line.index("print(\"") + 7:line.rindex("\")")])
							elif "print(" in line:
								printFlag = True
							elif printFlag:
								buffer += line
								if ")" in line:
									fetchPrompts(pythonFilePath, idx, functionFlag, line[line.index("print(\"") + 7:line.rindex("\")")])
									printFlag = False
						f.write("\\end{document}")
					endTime = time()
					generationTimeDelta = endTime - startTime
					print("The LaTeX generation for \"{0}\" finished in {1:.9f} second(s). ".format(pythonFilePath, generationTimeDelta))
					
					# LaTeX Compilation #
					try:
						startTime = time()
						process = Popen(["pdflatex", fileName], cwd = folderPath)
						endTime = time()
						compilationTimeDelta = endTime - startTime
						if process.wait() == EXIT_SUCCESS:
							print("The LaTeX compilation for \"{0}\" succeeded in {1:.9f} second(s). ".format(pythonFilePath, compilationTimeDelta))
							return True
						else:
							print("The LaTeX compilation for \"{0}\" failed. The time consumption is {1:.9f} second(s). ".format(pythonFilePath, compilationTimeDelta))
							return False
					except BaseException as compilationBE:
						print("The LaTeX compilation for \"{0}\" failed since {1}. ".format(pythonFilePath, compilationBE))
						return False
				except BaseException as generationBE:
					print("The LaTeX generation for \"{0}\" failed since {1}. ".format(pythonFilePath, generationBE))
					return False
			else:
				print("The TEX generation for \"{0}\" failed since the parent folder was not created successfully. ".format(pythonFilePath))
				return False
		else:
			print("The passed file \"{0}\" is not a Python file. ".format(pythonFilePath))
			return False
	else:
		print("The passed parameter should be a string. ")
		return False

def main() -> int:
	successCount, totalCount = 0, 0
	if len(argv) >= 3:
		print("As multiple options are provided, these options will be handled in the child processes. ")
		for mainTexPath in argv[1:]:
			totalCount += 1
			commandline = STARTUP_COMMAND_FORMAT.format(executable, __file__, mainTexPath)
			exitCode = os.system(commandline)
			print("$ {0} -> {1}".format(commandline, exitCode))
			if exitCode == EXIT_SUCCESS:
				successCount += 1
			print("The exit code provided here is inaccurate. Please refer to the exit codes of the child processes. ")
	elif len(argv) == 2:
		if os.path.isdir(argv[1]):
			for root, dirs, files in os.walk(argv[1]):
				for fileName in files:
					if os.path.splitext(fileName)[1].lower() == ".py" and "." != root:
						totalCount += 1
						successCount += int(generateSchemeTxt(os.path.join(root, fileName)))
		elif os.path.isfile(argv[1]) and os.path.splitext(argv[1])[1].lower() == ".py" and os.path.split(argv[1])[0] != os.path.abspath(os.path.dirname(__file__)):
			totalCount += 1
			if generateSchemeTxt(argv[1]):
				successCount += 1
		else:
			print("Cannot recognize the following option as a folder or a Python file. \n\t{0}".format(argv[1]))
	else:
		for root, dirs, files in os.walk("."):
			for fileName in files:
				if os.path.splitext(fileName)[1].lower() == ".py" and "." != root:
					totalCount += 1
					successCount += int(generateSchemeTxt(os.path.join(root, fileName)))
	iRet = EXIT_SUCCESS if totalCount and successCount == totalCount else EXIT_FAILURE
	print("\n")
	print("Successfully handled {0} / {1} {2} with a success rate of {3:.2f}%. ".format(successCount, totalCount, "items" if successCount > 1 else "item", successCount * 100 / totalCount) if totalCount else "Nothing was handled. ")
	print("Please press the enter key to exit ({0}). ".format(iRet))
	try:
		input()
	except:
		print()
	return iRet



if "__main__" == __name__:
	exit(main())