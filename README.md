# Cryptography-Protocols

Two proposed cryptography protocols with their baselines have been implemented here based on the Python (3.x) programming language and the Python charm library under the Ubuntu (24.04.1 LTS) operating system (WSL). 

A Python script for generating LaTeX files of protocols from Python scripts is also provided. 

A possible Python charm environment configuration tutorial in Chinese can be viewed at [https://blog.csdn.net/weixin_45726033/article/details/144254189](https://blog.csdn.net/weixin_45726033/article/details/144254189?_blank) if necessary. 

To test the Python charm environment initially, try to execute ``from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element`` in Python, which is also how all the Python scripts in this project import the necesssary libraries. 

An EOF (-1) signal will be returned to its parent process if the program lacks any of the necessary libraries. 

When there are hash functions, the following rules will be applied. 

- The function of the variable $\hat{H}$ is to hash something into a bit array whose length is the security parameter $\lambda$. Thus, an ``int`` object instead of an object belonging to any series data type is designed to store the bit array and accomplish the $\oplus$ operation to accelerate the $\oplus$ operation and reduce the memory consumption. 
- The message inputted to the ``Enc`` function can be an ``int`` or a ``bytes`` object, where the overflowed values will be cast by performing the ``&`` operation on the message and the operand indicating the maximum value of the limited count of bits.
- The ``str`` object is not accepted as a possible form of the message inputted to the ``Enc`` function since the encoding and decoding are not the things should be considered in these scripts. 
- The statement ``int.from_bytes(x, byteorder = "big")`` will be used to convert the ``bytes`` object into the ``int`` object if a ``bytes`` object is passed as the message for encryption. 
- The output of the ``Dec`` function is an ``int`` object. 

Otherwise, all the objects during the algebraic operations should belong to the ``Element`` type. 

#### generateProtocolLaTeX.py

This script helps convert each Python script into the corresponding LaTeX source file in the folder where the script is located. 

The script will try to finish the compilation once a LaTeX source file is generated. 

Usually, it will succeed if ``pdflatex`` is available and on the path. 
