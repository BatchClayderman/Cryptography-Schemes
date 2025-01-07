# Cryptography Schemes

Two proposed cryptography schemes with their baselines have been implemented here based on the Python (3.x) programming language and the Python charm library under the Ubuntu (24.04.1 LTS) operating system (WSL). 

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

For Linux developers and testers, the following command lines can be useful. 

- Execute ``find . -maxdepth 1 -type f -name "*.py" -exec python {} Y 0 \;`` in a Linux terminal to execute all the Python scripts in the corresponding scheme folder if you wish to execute a category of Python scripts. 
- Execute ``find . -maxdepth 2 -type f -name "*.py" -exec python {} Y 0 \;`` in a Linux terminal to execute all the Python scripts in the root folder of the cryptography schemes if you wish to execute all the Python scripts. 

Additionally, a Python script for generating LaTeX files of schemes from Python scripts is provided here. A possible Python charm environment configuration tutorial in Chinese can be viewed at [https://blog.csdn.net/weixin_45726033/article/details/144254189](https://blog.csdn.net/weixin_45726033/article/details/144254189) if necessary. If you are a Chinese beginner, [https://blog.csdn.net/weixin_45726033/article/details/144822018](https://blog.csdn.net/weixin_45726033/article/details/144822018) may be helpful. 

#### generateSchemeLaTeX.py

This script helps convert each Python script into the corresponding LaTeX source file in the folder where the script is located. 

The script will try to finish the compilation once a LaTeX source file is generated. 

Usually, it will succeed if ``pdflatex`` is available and on the path. 

For developers, this script will check the style of the Python scripts. 

#### Environment details

- [Ubuntu 24.04.1 LTS (WSL)](https://learn.microsoft.com/windows/wsl/install)
- [Python 3.12.3](https://www.python.org/)
- [GMP-6.3.0](https://gmplib.org/)
- [PBC-0.5.14](https://crypto.stanford.edu/pbc/download.html)
- OpenSSL library 3.0.13 (``sudo apt-get install libssl-dev``)
- [Python charm library](https://github.com/EliusSolis/charm)

#### Git issues

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

- **Push**
```
cd ~/Cryptography-Schemes
git add .
git commit -m Update
git push
```

Eventually, submit a Pull Request (PR) after pushing. If you are required to login during pushing, try to use ``gh`` (recommended) or generate a token from your GitHub account. 

## SchemeHIBME

Click [here](./SchemeHIBME/README.md) to view details. 

## SchemeIBMETR

Click [here](./SchemeIBMETR/README.md) to view details. 
