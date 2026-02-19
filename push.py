import os
from sys import exit
from subprocess import run
from datetime import datetime
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class GitPusher:
	def __init__(self:object, localRepositoryPath:str = ".") -> object:
		self.__gitFlag = False
		self.__localRepositoryPath = localRepositoryPath if isinstance(localRepositoryPath, str) else "."
	def initialize(self:object) -> bool:
		self.__gitFlag = False
		try:
			result = run(("git", "--version"), capture_output = True, text = True, cwd = self.__localRepositoryPath)
			if EXIT_SUCCESS == result.returncode and result.stdout.startswith("git version") and not result.stderr:
				self.__gitFlag = True
				print("Successfully initialized ``git``. ")
			else:
				print("Failed to initialize ``git``. \n\t{0}".format(result))
		except BaseException as e:
			print("Failed to initialize ``git``. \n\t{0}".format("KeyboardInterrupt" if isinstance(e, KeyboardInterrupt) else e))
		return self.__gitFlag
	def push(self:object) -> bool:
		if self.__gitFlag:
			commitMessage = "Regular Update (HKT {0})".format(datetime.now().strftime("%Y%m%d%H%M%S%f"))
			print("The commit message prepared is \"{0}\". ".format(commitMessage))
			result = run(("git", "add", "."), capture_output = True, text = True, cwd = self.__localRepositoryPath)
			if EXIT_SUCCESS == result.returncode and not result.stdout and not result.stderr:
				result = run(("git", "commit", "-m", commitMessage), capture_output = True, text = True, cwd = self.__localRepositoryPath)
				print(result.stdout.replace("nothing to commit, working tree clean", "").rstrip())
				if EXIT_SUCCESS == result.returncode or EXIT_FAILURE == result.returncode and "(use \"git push\" to publish your local commits)" in result.stdout:
					try:
						result = run(("git", "push"), cwd = self.__localRepositoryPath)
					except KeyboardInterrupt:
						print("\nFailed to execute \"git push\" due to KeyboardInterrupt. ")
						return False
					except BaseException as e:
						print("Failed to execute \"git push\". \n\t{0}".format(e))
						return False
					if EXIT_SUCCESS == result.returncode:
						print("Successfully pushed to GitHub. ")
						return True
					else:
						print("Failed to execute \"git push\". \n\t{0}".format(result))
						return False
				elif "nothing to commit, working tree clean" in result.stdout:
					print("Nothing to commit or push, the working tree is clean. ")
					return True
				else:
					print("Failed to execute \"git commit -m \"{0}\". \n\t{1}".format(commitMessage, result))
					return False
			else:
				print("Failed to execute \"git add .\". \n\t{0}".format(result))
				return False
		else:
			print("Please correctly deploy ``git`` on the device and run the ``.initialize`` method function before running the ``.push`` method function. ")
			return False


def main() -> int:
	gitPusher = GitPusher()
	if gitPusher.initialize():
		errorLevel = EXIT_SUCCESS if gitPusher.push() else EXIT_FAILURE
	else:
		errorLevel = EOF
	print("Please press the enter key to exit ({0}). ".format(errorLevel))
	try:
		input()
	except:
		print()
	print()
	return errorLevel



if __name__ == "__main__":
	exit(main())