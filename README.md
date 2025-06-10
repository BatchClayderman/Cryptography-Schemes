# Cryptography Schemes

Some proposed cryptography schemes with their baselines have been implemented here based on the Python (3.x) programming language and the Python charm library under the Ubuntu (24.04.1 LTS) operating system (WSL). 

## 1. Introduction

This section will first introduce the implementation and computation details. Subsequently, the way of converting the official Python scripts to LaTeX sources will be presented. Eventually, measurements and git issues will be discussed. 

### 1.1 Implementation details

Please deploy the Python (3.x) and the Python charm library environments correctly. 

A possible Python charm environment configuration tutorial in Chinese can be viewed at [https://blog.csdn.net/weixin_45726033/article/details/144254189](https://blog.csdn.net/weixin_45726033/article/details/144254189) if necessary. If you are a Chinese beginner, [https://blog.csdn.net/weixin_45726033/article/details/144822018](https://blog.csdn.net/weixin_45726033/article/details/144822018) may be helpful. 

To test the Python charm environment initially, try to execute ``from charm.toolbox.pairinggroup import PairingGroup, G1, G2, GT, ZR, pair, pc_element as Element`` in Python, which is also how all the Python scripts in this project import the necessary libraries. 

Here are the statements related to inputs and outputs, where the default round count is ``100`` and the default output file path corresponds to the Python file path. 

- If a scheme is applicable to symmetric and asymmetric groups of prime orders, curve types and security parameters in tuple ``("MNT159", "MNT201", "MNT224", "BN254", ("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))`` will be tested. 
- If a scheme is only applicable to symmetric groups of prime orders, curve types and security parameters in tuple ``(("SS512", 128), ("SS512", 160), ("SS512", 224), ("SS512", 256), ("SS512", 384), ("SS512", 512))`` will be tested. 
- The output files in the three-line table or plain text form should contain the input parameters, correctness-related counts, procedure time consumption, program memory consumption, storing sizes of elements from different fields, and storing sizes of important variables. 
- Users should only modify the ``# Begin #`` part in the ``main`` function if they just want to test different parameters. 

The rules of exit codes are as follows. 

- For all the Python scripts here, an ``EXIT_SUCCESS`` ($0$) signal will be returned to its parent process if some results are obtained and all the results pass all the tests. 
- For all the Python scripts here, an ``EXIT_FAILURE`` ($1$) signal will be returned to its parent process if no results are obtained or any of the results fail any of the tests. 
- For all the Python scripts here, an ``EOF`` ($-1$) signal will be returned to its parent process if the program lacks any of the necessary libraries. 

The rules of command lines are as follows. 

- The program scans the command-line options in sequence. 
  - If the option can be converted to an ``int`` object, the program will set the value as the countdown time after the program finishes running. 
  - Otherwise, the program will try to recognize whether the overwriting should have proceeded when an output already exists. 
- You can use ``inf`` or ``0`` to indicate an interactive or immediate action after the program finishes the scheme, respectively. 

The following command lines can be useful for executing one-stop testing. 

- Execute ``find . -maxdepth 1 -type f -name "*.py" -exec python {} Y 0 \;`` in a non-Windows terminal to execute all the Python scripts in the corresponding scheme folder if you wish to execute a category of Python scripts. 
- Execute ``find . -maxdepth 2 -type f -name "*.py" -exec python {} Y 0 \;`` in a non-Windows terminal to execute all the Python scripts in the root folder of the cryptography schemes if you wish to execute all categories of Python scripts.
- Add `` > /dev/null`` to the end of the command lines or use a screen if the printing affects the computation of the time consumption in a non-Windows terminal. 
- Execute ``for %f in (*.py) do python "%f" Y 0`` in a Windows terminal to execute all the Python scripts in the corresponding scheme folder if you wish to execute a category of Python scripts.
- Execute ``for /r %f in (*.py) do python "%f" Y 0`` in a Windows terminal to execute all the Python scripts in the root folder of the cryptography schemes if you wish to execute all categories of Python scripts. 
- Add `` > NUL`` to the end of the command lines if the printing affects the computation of the time consumption in a Windows terminal. 

If you wish to search a specified string throughout the whole repository in a local clone, the Linux command ``find .. -type f -name "*.py" -exec echo {} \; -exec grep "${stringsToBeSearched}" {} \;`` should be fine. 

### 1.2 Computation details

Normally, all the objects during the algebraic operations should belong to the ``Element`` type. However, most academic papers introduce other types but do not consider type conversion in a friendly way. A variable is treated as equivalent in different types, which can simultaneously complete all the Pairing operations and all other operations from all other types like $||$ and $\oplus$. Actually, this is incorrect. 

Meanwhile, most scholars believe that the design of the schemes is the most important aspect, rendering the engineering implementations perfunctory, not to mention that they will not consider the security verification and the type conversion. These details are actually time-consuming in actual programming and fatal during applications. 

Nowadays, many published implementations cannot run directly after they are downloaded. 

- Some of them are just due to outdated relies (V). 
- Some require feasible environment configurations or debugging (V). 
- Some are abstracted or interactive to let users specify values for important parameters before running due to programmability (V). 
- Some are modified not to run conveniently since their authors still want to benefit from them and publish more future papers, but have to open-source them (X). 
- Some are modified maliciously since their authors do not want the experiments re-implemented, where the results would be found to be fakes (X). 
- Some are fakes. 
- Some are inconsistent with or unrelated to the content of the paper (X). 
- Some even contain grammar errors (X). 

Anyway, re-implementing baselines is always a wise choice. Converting the baseline implementations using the aligned styles is also necessary, even though they can be downloaded and run directly. Therefore, we would like to offer as many computation details as possible here. 

#### 1.2.1 Type conversion

The rules of type conversion are as follows. 

- From ``int`` to ``bytes``: ``x.to_bytes(digitCount, byteorder = "big")`` (``digitCount`` is the byte length)
- From ``bytes`` to ``int``: ``int.from_bytes(x, byteorder = "big")``
- From ``Element`` to ``bytes``: pairingGroup.serialize(x)`` (``pairingGroup`` is an instance of ``PairingGroup``)
- From ``bytes`` to ``Element``: ``pairingGroup.hash(x, elementType)`` (``pairingGroup`` is an instance of ``PairingGroup`` while ``elementType`` can be ``ZR`` or ``G1`` only)
- Objects to be concatenated (Not matrix concatenation): Convert the objects to ``bytes`` to perform concatenation
- Objects to be $\oplus$: Convert the objects to ``int`` to perform $\oplus$

Among these conversion rules, only the following cases are equivalent. 

- For either an integer or a ``bytes`` object, converting to the other type, performing finite operations, and then converting back to the original type is equivalent to performing the same finite operations on the original type only when a specific byte length is fixed and the operation does not overflow that length. 
- Only when there are no additional operations, serializing and deserializing elements in the same group can produce the same elements as the original ones. 

#### 1.2.2 Series data type

Vectors, arrays, or lists in theory are stored as Python ``tuple`` objects in practice. This can help

- Avoid modifying variables inside a class from outside the class as much as possible; 
- Make the memory computation of an object of a series datum type as exact as possible (though no practical memory computation from the engineering aspect is officially embedded in the scripts here); 
- Reduce the time consumption since the index lookup is faster compared with the key-value pair one (especially in large dictionaries); and 
- Perform fair comparisons without using third-party libraries like the ``ndarray`` from the ``numpy`` library for matrix acceleration computation. 

#### 1.2.3 Hash functions

When there are hash functions, the following rules will be applied. 

- Some hash functions are designed to hash an element, integer, ``bytes``, etc. (of any bit length (``\| x \| = $\{0, 1\}^*$``)) into a bit array whose length is related to the security parameter $\lambda$ like ``$\{0, 1\}^\lambda$`` and ``$\{0, 1\}^{2\lambda}$``. We use some commonly seen hash functions like ``SHA512`` to accomplish the hashing after converting the objects to ``bytes`` (if necessary). 
- Some hash functions are designed to hash an integer, a ``bytes``, etc. (of any bit length (``\| x \| = $\{0, 1\}^*$``)) into an element of ``ZR`` or ``G1``. We use the ``hash`` from the ``PairingGroup`` to accomplish the hashing after converting the objects to ``bytes`` (if necessary). 
- The ``int`` object instead of any series datum type storing $\lambda$ ``bool`` value(s) is designed to store the bit array and accomplish the $\oplus$ operation to accelerate the $\oplus$ operation and reduce memory consumption.
- The bit arrays will be aligned to the right by being filled with 0's (``b"\0"`` or ``0b0``) on the left when they are of different lengths. As ``int`` objects are used for storing bit arrays and performing the $\oplus$ operation for binary strings, this will be done automatically during the ``int ^ int``. 
- The message inputted to the ``Enc`` function can be an ``int`` or a ``bytes`` object, where the overflowed values will be cast by performing the ``&`` operation on the message and the operand indicating the maximum value of the limited count of bits.
- The ``str`` object is not accepted as a possible form of the message inputted to the ``Enc`` function since the encoding and decoding are not the things that should be considered in these scripts. 
- The statement ``int.from_bytes(x, byteorder = "big")`` will be used to convert the ``bytes`` object into the ``int`` object if a ``bytes`` object is passed as the message for encryption. 
- The output of the ``Dec`` function is an ``int`` object. 

The following lines can handle the $\hat{H}$, which hashes an element to a ``bytes`` object with a length of $\lambda$ stored as an integer. 

```
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
	HHat = lambda x:int.from_bytes(sha512(self.__group.serialize(x)).digest() * (((self.__group.secparam - 1) >> 9) + 1), byteorder = "big") & self.__operand # $\hat{H}: \mathbb{G}_T \rightarrow \{0, 1\}^\lambda$
	print("Setup: An irregular security parameter ($\\lambda = {0}$) is specified. It is recommended to use 128, 160, 224, 256, 384, or 512 as the security parameter. ".format(self.__group.secparam))
```

#### 1.2.4 Product

Since Python does not have a built-in product function, the product function will be executed as follows. 

```
def __product(self:object, vec:tuple|list|set) -> Element:
	if isinstance(vec, (tuple, list, set)) and vec:
		element = vec[0]
		for ele in vec[1:]:
			element *= ele
		return element
	else:
		return self.__group.init(ZR, 1)
```

#### 1.2.5 Coefficient computation

The ``computeCoefficients`` function is used to compute the coefficients of the expand expression of the expressions like $F(x) = (x - x_1)(x - x_2)\cdots(x - x_d)$, that is, $F(x) = (x - x_1)(x - x_2)\cdots(x - x_d) = x^d - \left(\sum_\limits{i = 1}^d x_i\right) x^{d - 1} + \left(\sum_\limits{1 \leqslant i < j \leqslant d} x_i x_j \right) x^{d - 2} - \cdots + (-1)^d \prod\limits_{i = 1}^d x_i$. 

Although the numpy library provides such functions, we need to implement them manually to achieve the following targets. 

- Avoid unfair time computations for comparison purposes; 
- Arrange the coefficients from the constant term to the highest degree term; 
- Avoid computation errors caused by that ``0`` and ``1`` in Pairing algebraic operations are not the real ``0`` and ``1``, respectively; and
- Maintain the type of all the coefficients the same as that of the roots passed. 

Here come the issues of manual computing. If we directly compute the coefficients as the equation shown above, that is, to calculate the first-order sum, second-order sum, $\cdots$, and finally the highest-order sum based on the $\mathrm{C}_n^1, \mathrm{C}_n^2, \cdots, \mathrm{C}_n^n$ combinations of all the roots, it will take the computer will plenty of extra computing power to achieve the combinations in addition to the $n$ sum operations, whose overall time complexity is $O(\mathrm{C}_n^1 + \mathrm{C}_n^2 + \cdots + \mathrm{C}_n^n + n) = O(2^n - 1 + n) = O(2^n - 1 + n)$. This can cause large time consumption when the number of roots is large. That is to say, the time complexity increases explosively with the number of roots. The more roots there are, the greater the increase in time complexity will be for each additional root. Anyway, we need to design an efficient algorithm to calculate the polynomial coefficients from the polynomial roots. 

First, we need to look at a simple example. For $d = 3$ roots 2, 3, and 5, we have the following calculation process to iterate to avoid combinatorial multiplication.
To begin with, we need to see a simple example first. For $d = 3$ roots 2, 3, and 5, we have the following computing procedure to proceed iteration to avoid combinatorial multiplication. 

| Operation | [0] | [1] | [2] | [3] |
| - | - | - | - | - |
| Initial [1] + [0] * $d$ | 1 | 0 | 0 | 0 |
| [1] += 2 * [0] | 1 | 2 | 0 | 0 |
| [2] += 3 * [1] | 1 | 2 | 6 | 0 |
| [1] += 3 * [0] | 1 | 5 | 6 | 0 |
| [3] += 5 * [2] | 1 | 5 | 6 | 30 |
| [2] += 5 * [1] | 1 | 5 | 31 | 30 |
| [1] += 5 * [0] | 1 | 10 | 31 | 30 |
| Alternate $\pm$ signs | 1 | $-10$ | 31 | $-30$ |
| Reverse | $-30$ | 31 | $-10$ | 1 |

That is, we get $(x - 2)(x - 3)(x - 5) = -30 + 31x - 10x^2 + x^3$, which is correct. We can also note that the order in which the roots are processed can be random, as long as each root (not the value of the root) is processed and processed only once. 

More generally, according to the feature of the cyclic polynomial, let $\lbrace a, b, c\rbrace = \lbrace 2, 3, 5\rbrace$ denote the roots. The principle behind this can be shown as follows. 

| Operation | [0] | [1] | [2] | [3] |
| - | - | - | - | - |
| Initial [1] + [0] * $d$ | 1 | 0 | 0 | 0 |
| [1] += $a$ * [0] | 1 | $a$ | 0 | 0 |
| [2] += $b$ * [1] | 1 | $a$ | $ab$ | 0 |
| [1] += $b$ * [0] | 1 | $a + b$ | $ab$ | 0 |
| [3] += $c$ * [2] | 1 | $a + b$ | $ab$ | $abc$ |
| [2] += $c$ * [1] | 1 | $a + b$ | $ab + (a + b)c$ | $abc$ |
| that is | 1 | $a + b$ | $ab + ac + bc$ | $abc$ |
| [1] += $c$ * [0] | 1 | $a + b + c$ | $ab +ac + bc$ | $abc$ |
| Alternate $\pm$ signs | 1 | $-(a + b + c)$ | $ab +ac + bc$ | $-(abc)$ |
| Reverse | $-(abc)$ | $ab + ac + bc$ | $-(a + b + c)$ | 1 |

The coefficients here satisfy the coefficients expressed using the cyclic polynomial at the beginning of this subsubsection. The key point is that the result of multiplying the new root by the low-order sum happens to make up for the lack of the cyclic polynomial of the new root in the high-order sum, without duplication or omission. Thus, we have the following method. The method takes the roots and a constant other than the left-hand multiplication as input and outputs the coefficients. 

```
def __computeCoefficients(self:object, roots:tuple|list|set, w:None|Element = None) -> tuple:
	if isinstance(roots, (tuple, list, set)) and all(isinstance(root, Element) and root.type == ZR or isinstance(root, int) for root in roots):
		d = len(roots)
		coefficients = [self.__group.init(ZR, 1)] + [self.__group.init(ZR, 0)] * d
		for r in roots:
			for k in range(d, 0, -1):
				coefficients[k] += r * coefficients[k - 1]
		coefficients = [(-1) ** i * coefficients[i] for i in range(d, -1, -1)]
		if isinstance(w, Element) and w.type == ZR  or isinstance(w, int):
			coefficients[-1] += w * self.__group.init(G1, 1)
		return tuple(coefficients)
	else:
		return (self.__group.init(ZR, 1), )
```

The time complexity of this algorithm is $O(n^2)$. As the inner loop starts from ``coefficients[cnt]`` where ``cnt`` is the current count of the roots that are proceeded and being proceeded, we can use the ``cnt`` to optimize the method to $O\left(\cfrac{n(n + 1)}{2}\right)$. An improved method is shown as follows, with bitwise operations used for optimization. 

```
def __computeCoefficients(self:object, roots:tuple|list|set, w:None|Element = None) -> tuple:
	if isinstance(roots, (tuple, list, set)) and all(isinstance(root, Element) and root.type == ZR or isinstance(root, int) for root in roots):
		d, cnt = len(roots), 1
		coefficients = [self.__group.init(ZR, 1)] + [self.__group.init(ZR, 0)] * d
		for r in roots:
			for k in range(cnt, 0, -1):
				coefficients[k] += r * coefficients[k - 1]
			cnt += 1
		coefficients = [-coefficients[i] if i & 1 else coefficients[i] for i in range(d, -1, -1)]
		if isinstance(w, Element) and w.type == ZR  or isinstance(w, int):
			coefficients[0] += w
		return tuple(coefficients)
	else:
		return (w, )
```

After multiple experiments, we found the following issues, some of which led to computation errors in coefficient computation and polynomial computation. Especially, the polynomial computation result of one of the roots based on the corresponding coefficients figured out is always non-zero. 

- When ZR elements are used to express the coefficients, the following issues occur. 
  - ``self.__group.init(ZR, 1)`` multiplied by the ZR element from the same ``PairingGroup`` object does not equal to the ZR element itself. 
  - Although some implementations ask users to specify ``0`` and ``1`` in the ZR field, the polynomial computation result of one of the roots, based on the corresponding coefficients figured out, is still always non-zero. 
- When G1 elements are used to express the coefficients, the following issues occur. 
  - ``self.__group.init(G1, 1)`` shows ``O``, and it is multiplied by any ZR element, integer, or ``float`` object is always ``O``. 
  - While ``self.__group.init(G1, 1)`` (``O``) plus any G1 element is the G1 element itself, ``O`` multiplied by any G1 element itself is also the G1 element, which is strange. 
- Exponentiation does not appear to be a repetition of multiplication. 
  - Neither ``x ** 2`` nor ``x ** self.__group.init(ZR, 2)`` is the same as ``x * x`` for any ``x`` belonging to the ``Element`` type. 
  - While ``2 == self.__group.init(ZR, 2)`` returns ``False``, ``x ** 2`` returns the same as ``x ** self.__group.init(ZR, 2)`` where ``x`` is a G1 element, which is strange. 
- The type of roots passed to the method is limited, which is not flexible enough. 
- $\cdots$

Therefore, we have to avoid using the ``1`` or ``0`` in any coefficient computation in ``PairingGroup`` environments. The final method is shown as follows. 

```
def __computeCoefficients(self:object, roots:tuple|list|set, w:Element|int|float|None = None) -> tuple:
	flag = False
	if isinstance(roots, (tuple, list, set)) and roots:
		d = len(roots)
		if isinstance(roots[0], Element) and all(isinstance(root, Element) and root.type == roots[0].type for root in roots):
			flag, coefficients = True, [self.__group.init(roots[0].type, 1), roots[0]] + [None] * (d - 1)
			constant = w if isinstance(w, Element) and w.type == roots[0].type else None
		elif isinstance(roots[0], (int, float)) and all(isinstance(root, (int, float)) for root in roots) and isinstance(w, (int, float)):
			flag, coefficients = True, [1, roots[0]] + [None] * (d - 1)
			constant = w if isinstance(w, (int, float)) else None
	if flag:
		cnt = 2
		for r in roots[1:]:
			coefficients[cnt] = r * coefficients[cnt - 1]
			for k in range(cnt - 1, 1, -1):
				coefficients[k] += r * coefficients[k - 1]
			coefficients[1] += r
			cnt += 1
		if constant is not None:
			coefficients[-1] += -constant if d & 1 else constant
		return tuple(-coefficients[i] if i & 1 else coefficients[i] for i in range(d, -1, -1))
	else:
		return (w, )
```

The corresponding procedures of the final method are shown as follows. In this problem, the coefficient of the highest-order term is always $1$, which should be omitted to save space complexity. Nonetheless, in practice, it is retained to meet the academic program specifications and space measurement requirements. By the way, this ``1`` is assigned to the corresponding ``1`` according to the type of the roots, and it never involves any computation throughout the script. 

| Operation | [0] | [1] | [2] | [3] |
| - | - | - | - | - |
| Initial [1] + [None] * $d$ | 1 | None | None | None |
| [1] = $a$ | 1 | $a$ | 0 | 0 |
| [2] = $b$ * [1] | 1 | $a$ | $ab$ | 0 |
| [1] += $b$ | 1 | $a + b$ | $ab$ | 0 |
| [3] = $c$ * [2] | 1 | $a + b$ | $ab$ | $abc$ |
| [2] += $c$ * [1] | 1 | $a + b$ | $ab + (a + b)c$ | $abc$ |
| that is | 1 | $a + b$ | $ab + ac + bc$ | $abc$ |
| [1] += $c$ | 1 | $a + b + c$ | $ab +ac + bc$ | $abc$ |
| Alternate $\pm$ signs | 1 | $-(a + b + c)$ | $ab +ac + bc$ | $-(abc)$ |
| Reverse | $-(abc)$ | $ab + ac + bc$ | $-(a + b + c)$ | 1 |

#### 1.2.6 Polynomial computation

The polynomial computation here refers to the computation of $F(x)$ mentioned in the previous subsubsection based on the corresponding coefficients figured out. At first, the computation is accomplished by ``sum(coefficients[i] * x ** i for i in range(d + 1))``. 

However, since neither ``x ** 2`` nor ``x ** self.__group.init(ZR, 2)`` is the same as ``x * x`` for any ``x`` belonging to the ``Element`` type, the following method is designed. 

```
def __computePolynomial(self:object, x:Element, coefficients:tuple|list) -> Element:
	if isinstance(x, Element) and x.type == ZR and isinstance(x, int) and isinstance(coefficients, (tuple, list)) and all(isinstance(coefficient, Element) and coefficient.type == ZR and isinstance(coefficient, int) for coefficient in coefficients):
		eleResult = coefficients[0]
		for i in range(1, len(coefficients)):
			eResult = self.__group.init(ZR, 1)
			for _ in range(i):
				eResult *= x
			eleResult += coefficients[i] * eResult
		return eleResult
	else:
		return self.__group.init(ZR, 0)
```

However, due to similar issues, this method is revised as follows. The $d$ here corresponds to that in the coefficient computation. Similarly, the coefficient of the highest-order term, $1$, never involves any computation throughout the script. 

```
def __computePolynomial(self:object, x:Element|int|float, coefficients:tuple|list) -> Element|int|float|None:
	if isinstance(coefficients, (tuple, list)) and coefficients and (															\
		isinstance(x, Element) and all(isinstance(coefficient, Element) and coefficient.type == x.type for coefficient in coefficients)	\
		or isinstance(x, (int, float)) and all(isinstance(coefficient, (int, float)) for coefficient in coefficients)						\
	):
		d, eleResult = len(coefficients) - 1, coefficients[0]
		for i in range(1, d):
			eResult = x
			for _ in range(i - 1):
				eResult *= x
			eleResult += coefficients[i] * eResult
		eResult = x
		for _ in range(d - 1):
			eResult *= x
		eleResult += eResult
		return eleResult
	else:
		return None
```

#### 1.2.7 Concatenation for multiple objects

On some occasions, we need to concatenate multiple objects, acting as byte concatenation. Please kindly refer to the following lines. 

```
def __concat(self:object, *vector:tuple|list) -> bytes:
	abcBytes = b""
	if isinstance(vector, (tuple, list)):
		for item in vector:
			if isinstance(item, (tuple, list)):
				abcBytes += self.__concat(*item)
			elif isinstance(item, Element):
				abcBytes += self.__group.serialize(item)
			elif isinstance(item, bytes):
				abcBytes += item
			else:
				try:
					abcBytes += bytes(item)
				except:
					pass
	return abcBytes
```

#### 1.2.8 Time consumption comparison for different implementations of the same solution

Generally speaking, in a unified computing environment, bitwise operations with the same number of operations will be faster than general addition, subtraction, multiplication, and division. In some cases, equivalent bit operations may require additional processing to achieve a certain function. This may result in the overall operation being inferior to the solution without bit operations. Therefore, the time comparison is required. 

The following Python script can be used to compare different implementations of the same solution in time consumption. You can select to use the optimal one in practice after comparing via this script. 

```
from sys import exit
from math import ceil
from time import perf_counter
EXIT_SUCCESS = 0
EXIT_FAILURE = 1


class Algorithms:
	@staticmethod
	def func1(n):
		for i in range(n):
			ceil(i / 8)
	@staticmethod
	def func2(n):
		for i in range(n):
			(i + 7) >> 3


def main():
	n = 100000000
	d = {algorithm:float("inf") for algorithm in dir(Algorithms) if "__" not in algorithm}
	for func in list(d.keys()):
		startTime = perf_counter()
		exec("Algorithms.{0}({1})".format(func, n))
		endTime = perf_counter()
		timeDelta = endTime - startTime
		d[func] = timeDelta
		print("Finished executing {0} in {1:.9f} second(s). ".format(func, timeDelta))
	print("The optimal algorithm is {0}. ".format(sorted(d.items(), key = lambda x:x[1])[0][0]))
	print("Please press the enter key to exit. ")
	try:
		input()
	except:
		print()
	return EXIT_SUCCESS



if "__main__" == __name__:
	exit(main())
```

### 1.3 Measurements

To compute the time consumption (time complexity) of a code set, please refer to the following lines. Remember to perform a division if a procedure contains computation for multiple objects, while only the computation procedure of one of those objects should be counted. 

```
from time import perf_counter

startTime = perf_counter()
# Your codes
endTime = perf_counter()
timeDelta = endTime - startTime # second(s)
```

To compute the memory consumption (space complexity) of a variable for academic purposes (actually, the byte length of the serialized element), please refer to the following lines. The code ``(group.secparam + 7) >> 3`` is a consideration of $\lambda$ values that do not meet $8 | \lambda$. After filling several bytes, any remaining one or more bits will occupy an additional byte, even if they do not form a complete byte. Specifically, some hash functions and concatenated ``bytes`` objects may return an integer whose actual byte length is longer than $\lambda$. This case is seldom, but actually exists. When designing the measurement function in the scripts containing such a situation, the space complexity of the special variables needs to be assigned manually.  

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
		return (group.secparam + 7) >> 3
	else:
		return -1
```

To compute the memory consumption (space complexity) of a variable for engineering purposes, please refer to the following lines. These codes are not used in the official implementations of the cryptography schemes here. Please adjust the codes in your own repositories if you wish to compute this measurement. 

```
from sys import getsizeof

s = getsizeof(group.random(ZR)) # Byte(s)
```

To compute the overall runtime memory consumption (space complexity) of the Python program, please refer to the following lines. These codes are not used in the official implementations of the cryptography schemes here. Please adjust the codes in your own repositories if you wish to compute this measurement. 

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

### 1.4 ``generateSchemeLaTeX.py``

A Python script for generating LaTeX source files of schemes from Python scripts is provided here. This script helps convert each Python script into the corresponding LaTeX source file in the folder where the script is located. 

The script will try to finish the compilation once a LaTeX source file is generated. Usually, it will succeed if ``pdflatex`` is available and on the path. 

For developers, this script will check the style of the Python scripts. Please use ``echo "" | python generateSchemeLaTeX.py | grep "^Detail: "`` to help check the non-unified prompts if necessary. 

### 1.5 Git issues

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

Eventually, submit a Pull Request (PR) after pushing. If you are required to log in while pushing, try to use ``gh`` (recommended) or generate a token from your GitHub account. 

## 2. SchemeAAIBME

Click [here](./SchemeAAIBME/README.md) to view details. 

Here are the equivalent implementations in the Java programming language based on the JPBC library. 

- Baselines: 
  - [https://github.com/BatchClayderman/Fuzzy_IB_ME](https://github.com/BatchClayderman/Fuzzy_IB_ME)
  - [https://github.com/BatchClayderman/Fuzzy_ME](https://github.com/BatchClayderman/Fuzzy_ME)
- Proposed: 
  - [https://github.com/BatchClayderman/AA-IB-ME](https://github.com/BatchClayderman/AA-IB-ME)

Regardless, using the implementations in the Python programming language is more encouraging. Out-of-date Java implementations can contain potential errors. 

## 3. SchemeCANIFPPCT

Click [here](./SchemeCANIFPPCT/README.md) to view details. 

Here are the equivalent implementations in the Java programming language based on the JPBC library. 

- Baselines: 
  - Version 1: [https://github.com/BatchClayderman/FEPPCT](https://github.com/BatchClayderman/FEPPCT)
  - Version 2: [https://github.com/BatchClayderman/CA-NI-PSI](https://github.com/BatchClayderman/CA-NI-PSI)

- Proposed: 
  - Version 1: [https://github.com/BatchClayderman/II-FPPCT](https://github.com/BatchClayderman/II-FPPCT)
  - Version 2: [https://github.com/BatchClayderman/CA-NI-FPPCT](https://github.com/BatchClayderman/CA-NI-FPPCT)

Regardless, using the implementations in the Python programming language is more encouraging. Out-of-date Java implementations can contain potential errors. 

## 4. SchemeHIBME

Click [here](./SchemeHIBME/README.md) to view details. 

## 5. SchemeIBMEMR

Click [here](./SchemeIBMEMR/README.md) to view details. 

## 6. SchemeIBMETR

Click [here](./SchemeIBMETR/README.md) to view details. 

## 7. SchemeIBPRME

Click [here](./SchemeIBPRME/README.md) to view details. 

## 8. Others

Here are some links to my other implemented cryptography schemes, which do not involve the Python charm library. 

By the way, this is not one of the major academic authors of the schemes mentioned in this section. Please only query here about the practical implementations. Thanks. 

### 8.1 C/C++

Here are some links to my other implemented cryptography schemes, which are in the C/C++ programming languages. 

1) OPSI-CA-ull: [https://github.com/BatchClayderman/OPSI-CA-ull](https://github.com/BatchClayderman/OPSI-CA-ull)
2) PSI-CA-ull: [https://github.com/BatchClayderman/PSI-CA-ull](https://github.com/BatchClayderman/PSI-CA-ull)
3) SPSI-CA-ull: [https://github.com/BatchClayderman/SPSI-CA-ull](https://github.com/BatchClayderman/SPSI-CA-ull)
4) VPSI-CA-ull: [https://github.com/BatchClayderman/VPSI-CA-ull](https://github.com/BatchClayderman/VPSI-CA-ull)

### 8.2 Java

Here is a link to my other implemented cryptography scheme, which is in the Java programming language based on the JPBC library. 

- GRS: [https://github.com/BatchClayderman/GRS](https://github.com/BatchClayderman/GRS)

### 8.3 Python

Here are some links to my other implemented cryptography schemes, which are in the Python programming language but not based on the Python charm library. 

1) LB-PEAKS: [https://github.com/BatchClayderman/LB-PEAKS](https://github.com/BatchClayderman/LB-PEAKS)
2) LLRS: [https://github.com/BatchClayderman/LLRS](https://github.com/BatchClayderman/LLRS)
3) FS-MUAEKS: [https://github.com/BatchClayderman/FS-MUAEKS](https://github.com/BatchClayderman/FS-MUAEKS)

## 9. Acknowledgment

The experimental environment details are as follows. Thanks to the developers for their hard work. 

- [Ubuntu 24.04.1 LTS (WSL)](https://learn.microsoft.com/windows/wsl/install)
- [Python 3.12.3](https://www.python.org/)
- [GMP-6.3.0](https://gmplib.org/)
- [PBC-0.5.14](https://crypto.stanford.edu/pbc/download.html)
- [OpenSSL library 3.0.13](https://www.openssl.org/) (``sudo apt-get install libssl-dev``)
- [Official Python charm library](https://github.com/JHUISI/charm)
- [Python charm library adapted to Python 3.12.x](https://github.com/EliusSolis/charm) (merged to the official one on January 23rd)

Thanks to [Department of Computer Science](https://www.cs.hku.hk/), [School of Computing and Data Science](https://www.cds.hku.hk/), [The University of Hong Kong](https://www.hku.hk/). 
