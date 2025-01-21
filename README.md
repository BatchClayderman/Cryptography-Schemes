# Cryptography Schemes

Some proposed cryptography schemes with their baselines have been implemented here based on the Python (3.x) programming language and the Python charm library under the Ubuntu (24.04.1 LTS) operating system (WSL). 

## 1. Introduction

To test the Python charm environment initially, try to execute ``from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element`` in Python, which is also how all the Python scripts in this project import the necessary libraries. 

The rules of exit codes are as follows. 
- For all the Python scripts here, an EXIT_SUCCESS ($0$) signal will be returned to its parent process if some results are obtained and all the results pass all the tests. 
- For all the Python scripts here, an EXIT_FAILURE ($1$) signal will be returned to its parent process if no results are obtained or any of the results fail any of the tests. 
- For all the Python scripts here, an EOF ($-1$) signal will be returned to its parent process if the program lacks any of the necessary libraries. 

Vectors, arrays, or lists in theory are stored as Python ``tuple`` objects in practice. This can help: 
- avoid modifying variables inside a class from outside the class as much as possible; 
- make the memory computation of an object of a series datum type as exact as possible; 
- reduce the time consumption since the index lookup is faster compared with the key-value pair one (especially in large dictionaries); and 
- perform fair comparisons without using third-party libraries like the ``ndarray`` from the ``numpy`` library for matrix acceleration computation. 

When there are hash functions, the following rules will be applied. 

- The function of the variable $\hat{H}$ in theory is to hash an element of any bit length ($\{0, 1\}^*$) into a bit array whose length is the security parameter $\lambda$ ($\{0, 1\}^\lambda$). Thus, the ``int`` object instead of any series datum type storing $\lambda$ ``bool`` values is designed to store the bit array and accomplish the $\oplus$ operation to accelerate the $\oplus$ operation and reduce memory consumption.
- The bit arrays will be aligned to the right by being filled with 0's (``b"\0"`` or ``0b0``) on the left when they are in different lengths. As ``int`` objects are used for storing bit arrays and performing the $\oplus$ operation for binary strings, this will be done automatically during the ``int ^ int``. 
- The message inputted to the ``Enc`` function can be an ``int`` or a ``bytes`` object, where the overflowed values will be cast by performing the ``&`` operation on the message and the operand indicating the maximum value of the limited count of bits.
- The ``str`` object is not accepted as a possible form of the message inputted to the ``Enc`` function since the encoding and decoding are not the things should be considered in these scripts. 
- The statement ``int.from_bytes(x, byteorder = "big")`` will be used to convert the ``bytes`` object into the ``int`` object if a ``bytes`` object is passed as the message for encryption. 
- The output of the ``Dec`` function is an ``int`` object. 

Otherwise, all the objects during the algebraic operations should belong to the ``Element`` type. 

Here are the statements related to inputs and outputs, where the default round count is ``20`` and the default output file path corresponds to the Python file path. 

- If a scheme is applicable to symmetric and asymmetric groups of prime orders, curve types and security parameters in tuple ``("MNT159", "MNT201", "MNT224", "BN254", ("SS512", 512))`` will be tested. 
- If a scheme is only applicable to symmetric groups of prime orders, curve types and security parameters in tuple ``(("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))`` will be tested. 
- The output files in the three-line table or plain text form should contain the input parameters, correctness-related counts, procedure time consumption, program memory consumption, storing sizes of elements from different fields, and storing sizes of important variables. 

The following command lines can be useful for executing one-stop testing. 

- Execute ``find . -maxdepth 1 -type f -name "*.py" -exec python {} Y 0 \;`` in a non-Windows terminal to execute all the Python scripts in the corresponding scheme folder if you wish to execute a category of Python scripts. 
- Execute ``find . -maxdepth 2 -type f -name "*.py" -exec python {} Y 0 \;`` in a non-Windows terminal to execute all the Python scripts in the root folder of the cryptography schemes if you wish to execute all categories of Python scripts.
- Add `` > /dev/null`` to the end of the command lines or use a screen if the printing affects the computation of the time consumption in a non-Windows terminal. 
- Execute ``for %f in (*.py) do python "%f" Y 0`` in a Windows terminal to execute all the Python scripts in the corresponding scheme folder if you wish to execute a category of Python scripts.
- Execute ``for /r %f in (*.py) do python "%f" Y 0`` in a Windows terminal to execute all the Python scripts in the root folder of the cryptography schemes if you wish to execute all categories of Python scripts. 
- Add `` > NUL`` to the end of the command lines if the printing affects the computation of the time consumption in a Windows terminal. 

Additionally, a Python script for generating LaTeX files of schemes from Python scripts is provided here. A possible Python charm environment configuration tutorial in Chinese can be viewed at [https://blog.csdn.net/weixin_45726033/article/details/144254189](https://blog.csdn.net/weixin_45726033/article/details/144254189) if necessary. If you are a Chinese beginner, [https://blog.csdn.net/weixin_45726033/article/details/144822018](https://blog.csdn.net/weixin_45726033/article/details/144822018) may be helpful. 

### 1.1 ``generateSchemeLaTeX.py``

This script helps convert each Python script into the corresponding LaTeX source file in the folder where the script is located. 

The script will try to finish the compilation once a LaTeX source file is generated. 

Usually, it will succeed if ``pdflatex`` is available and on the path. 

For developers, this script will check the style of the Python scripts. 

### 1.2 Measurements

To compute the time consumption (time complexity) of a set of codes, please refer to the following codes. 

```
from time import perf_counter

startTime = perf_counter()
# Your codes
endTime = perf_counter()
timeDelta = endTime - startTime # second(s)
```

To compute the memory consumption (space complexity) of a variable for academic purposes (actually the byte length of the serialized element), please refer to the following codes. 

```
def getLengthOf(group:object, obj:Element|tuple|list|set|bytes|int) -> int: # Byte(s)
	if isinstance(obj, Element):
		return len(group.serialize(obj))
	elif isinstance(obj, (tuple, list, set)):
		sizes = tuple(getLengthOf(o) for o in obj)
		return -1 if -1 in sizes else sum(sizes)
	elif isinstance(obj, bytes):
		return len(obj)
	elif isinstance(obj, int) or callable(obj):
		return group.secparam >> 3
	else:
		return -1
```

To compute the memory consumption (space complexity) of a variable for engineering purposes, please refer to the following codes. 

```
from sys import getsizeof

s = getsizeof(group.random(ZR)) # Byte(s)
```

To compute the overall runtime memory consumption (space complexity) of the Python program, please refer to the following codes. 

```
import os
try:
	from psutil import Process
except:
	print("Cannot compute the memory via ``psutil.Process``. ")
	print("Please try to install the ``psutil`` library via ``python -m pip install psutil`` or ``apt-get install python3-psutil``. ")
	print("Please press the enter key to exit. ")
	input()
	exit(-1)

process = Process(os.getpid())
memory = process.memory_info().rss # Byte(s)
```

### 1.3 Git issues

If you wish to clone the project, try to use the following command lines. 

```
cd ~
git clone https://github.com/BatchClayderman/Cryptography-Schemes.git
```

If you wish to synchronize this project to the local machine after cloning, try to use the following command lines. 

```
cd ~/Cryptography-Schemes
git pull
```

If you wish to contribute to this project, try to use the following command lines after forking this project to your own GitHub account, where the ``XXX`` stands for your account. 

- **Clone**: 
```
cd ~
git clone https://github.com/XXX/Cryptography-Schemes.git
```

- **Pull**: 
```
cd ~/Cryptography-Schemes
git pull
```

- **Push**: 
```
cd ~/Cryptography-Schemes
git add .
git commit -m Update
git push
```

Eventually, submit a Pull Request (PR) after pushing. If you are required to log in during pushing, try to use ``gh`` (recommended) or generate a token from your GitHub account. 

## 2. SchemeCANIFPPCT

Click [here](./SchemeCANIFPPCT/README.md) to view details. 

Here are the equivalent implementations in Java programming language based on the JPBC library. 

- Baselines
  - Version 1: [https://github.com/BatchClayderman/FEPPCT](https://github.com/BatchClayderman/FEPPCT)
  - Version 2: [https://github.com/BatchClayderman/CA-NI-PSI](https://github.com/BatchClayderman/CA-NI-PSI)

- Proposed
  - Version 1: [https://github.com/BatchClayderman/II-FPPCT](https://github.com/BatchClayderman/II-FPPCT)
  - Version 2: [https://github.com/BatchClayderman/CA-NI-FPPCT](https://github.com/BatchClayderman/CA-NI-FPPCT)

Anyway, it is still encouraging to use the implementations in Python programming language. 

## 3. SchemeHIBME

Click [here](./SchemeHIBME/README.md) to view details. 

## 4. SchemeIBMETR

Click [here](./SchemeIBMETR/README.md) to view details. 

## 5. Others

Here are some links to my other implemented cryptography schemes, which do not involve the Python charm library. 

By the way, this is not one of the major academic authors of the schemes mentioned in this section. Please only query here about the practical implementations. Thanks. 

### 5.1 C/C++

Here are some links to my other implemented cryptography schemes, which are in C/C++ programming language. 

1) OPSI-CA-ull: [https://github.com/BatchClayderman/OPSI-CA-ull](https://github.com/BatchClayderman/OPSI-CA-ull)
2) PSI-CA-ull: [https://github.com/BatchClayderman/PSI-CA-ull](https://github.com/BatchClayderman/PSI-CA-ull)
3) SPSI-CA-ull: [https://github.com/BatchClayderman/SPSI-CA-ull](https://github.com/BatchClayderman/SPSI-CA-ull)
4) VPSI-CA-ull: [https://github.com/BatchClayderman/VPSI-CA-ull](https://github.com/BatchClayderman/VPSI-CA-ull)

### 5.2 Java

Here is a link to my other implemented cryptography scheme, which is in Java programming language based on the JPBC library. 

- GRS: [https://github.com/BatchClayderman/GRS](https://github.com/BatchClayderman/GRS)

### 5.3 Python

Here are some links to my other implemented cryptography schemes, which are in Python programming language but not based on the Python charm library. 

1) LB-PEAKS: [https://github.com/BatchClayderman/LB-PEAKS](https://github.com/BatchClayderman/LB-PEAKS)
2) LLRS: [https://github.com/BatchClayderman/LLRS](https://github.com/BatchClayderman/LLRS)
3) FS-MUAEKS: [https://github.com/BatchClayderman/FS-MUAEKS](https://github.com/BatchClayderman/FS-MUAEKS)

## 6. Acknowledgment

The experimental environment details are as follows. Thanks to the developers for their hard work. 

- [Ubuntu 24.04.1 LTS (WSL)](https://learn.microsoft.com/windows/wsl/install)
- [Python 3.12.3](https://www.python.org/)
- [GMP-6.3.0](https://gmplib.org/)
- [PBC-0.5.14](https://crypto.stanford.edu/pbc/download.html)
- [OpenSSL library 3.0.13](https://www.openssl.org/) (``sudo apt-get install libssl-dev``)
- [Official Python charm library](https://github.com/JHUISI/charm)
- [Python charm library adapted to Python 3.12.x](https://github.com/EliusSolis/charm)

Thanks to [Department of Computer Science](https://www.cs.hku.hk/), [School of Computing and Data Science](https://www.cds.hku.hk/), [The University of Hong Kong](https://www.hku.hk/). 
