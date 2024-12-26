# Cryptography-Protocols

Some cryptography protocols have been implemented based on the Python charm library here. 

### HIB-ME

#### ProtocolAnonymousIBE.py

The implementation of Anonymous Hierarchical Identity-based Encryption 

[https://github.com/BatchClayderman/ProtocolHIBME](https://github.com/BatchClayderman/ProtocolHIBME)

# Protocols

There are three cryptography protocols implemented here based on the Python programming language and the Python charm library under the Ubuntu (24.04.1 LTS) operating system (WSL). 

A Python script for generating LaTeX files of protocols from Python scripts is also provided. 

A possible Chinese Python charm environment configuration tutorial can be viewed at [https://blog.csdn.net/weixin_45726033/article/details/144254189](https://blog.csdn.net/weixin_45726033/article/details/144254189) if necessary. 

When there are hash functions, the following rules will be applied. 

- The message inputted to the ``Enc`` function can be an ``int`` or a ``bytes`` object, where the overflowed values will be cast by performing the ``&`` operation on the message and the operand indicating the maximum value of the limited count of bits. 
- The ``str`` object is not accepted as a possible form of the message inputted to the ``Enc`` function since the encoding and decoding are not the things should be considered in these scripts. 
- The output of the ``Dec`` function is an ``int`` object. 

### ProtocolAnonymousME.py

This is the implementation of the anonymous ME protocol based on the Python programming language. 

### ProtocolHIBME.py

This is the implementation of the HIB-ME protocol based on the Python programming language. 

### ProtocolIBMETR.py

This is the implementation of the IBMETR protocol based on the Python programming language. 

### generateProtocolLaTeX.py

This script helps convert the Python codes into LaTeX source codes. 

If ``pdflatex`` is available and on the path, the compilation can be automatically finished. 
