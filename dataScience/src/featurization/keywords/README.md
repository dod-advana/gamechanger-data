rake - Rapid Automatic Keyword Extraction
=========================================

An efficient Python implementation of the Rapid Automatic Keyword Extraction (RAKE)
algorithm as described
in: Rose, S., Engel, D., Cramer, N., & Cowley, W. (2010).
_Automatic Keyword Extraction from Individual Documents_. nn M. W. Berry & J. Kogan - (Eds.), Text Mining: Theory and Applications: John Wiley & Sons.

Different versions of this algorithm have been floating around GitHub for
quite a while. This version attempts to improve its efficiency while preserving
the essence of the original algorithm.
The source code was originally released under the MIT License.

### Stop Words
There are three builtin options for stop word lists: 'smart', 'google', and 'nltk'.
The default stop word list is 'google'. The 'nltk' and 'google' stop words are
very similar. 
The 'smart' stop words contain articles and some verbs. The
results resemble those when noun chunks are considered for keywords. All
stop word lists are represented as optimized regular expressions.

## License
Copyright (c) 2013 - 2019 - Chris SKiscim

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

