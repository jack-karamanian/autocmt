#!/usr/bin/env python
import sys

class DocBlockInfo:
	def __init__(self, name, args):
		self._name = name
		self._args = args
	@property
	def name(self):
		return self._name
	@property
	def args(self):
		return self._args

class DocBlockComment:
	def __init__(self, line, comment):
		self._line = line
		self._comment = comment
	@property
	def line(self):
	    return self._line
	@property
	def comment(self):
	    return self._comment

def doc_block_comment(info):
	result = "/****************************************************************\n\n"
	result = result + "\tFUNCTION: %s\n\n" %(info.name)
	result = result + "\tARGUMENTS: \n"
	for arg in info.args:
		result = result + "\t\t%s - \n" % (arg)
	result = result + "\n"
	result = result + "\tRETURNS: \n\n"
	result = result + "\tNOTES: \n"
	result = result + "****************************************************************/\n"
	return result

def is_commentable(node):
	"""True if the function/method is to be documented according to
		the standards of CSCI 241"""
	from clang.cindex import CursorKind
	kind = node.kind
	return node.is_definition() and (kind == CursorKind.CXX_METHOD or kind == CursorKind.CONSTRUCTOR or kind == CursorKind.DESTRUCTOR or kind == CursorKind.FUNCTION_DECL)

def get_commentable_cursors(node):
	"""Get all cursors for which is_commentable is true"""
	cursors = []
	kind = node.kind
	if is_commentable(node):
		cursors.append(node)
	for child in node.get_children():
		for n in get_commentable_cursors(child):
			cursors.append(n)
	return cursors

def get_doc_block_info(cursor):
	"""Get the documentation box comment with the line in a DocBlockInfo"""
	parentScope = cursor.semantic_parent.spelling or ""
	if parentScope != "":
		parentScope = parentScope + "::"

	# Get the names of each argument
	args = [arg.spelling for arg in cursor.get_arguments()]
	const = str()
	# To do
	if cursor.type.is_const_qualified():
		const = " const"

	return DocBlockInfo(parentScope + cursor.spelling + const, args)

def get_doc_comments(cursor, sourceFileName):
	docCmts = []
	for node in get_commentable_cursors(cursor):
		# Only use functions defined in the current file
		if node.location.file.name == sourceFileName:
			commentInfo = get_doc_block_info(node)
			docCmts.append(DocBlockComment(node.location.line, doc_block_comment(commentInfo)))
	return docCmts

def source_with_doc_blocks(fileName, docBlocks):
	lines = []
	result = str();

	# Get all lines in the file
	with open(fileName, "r") as file:
		lines = file.readlines()

	# Insert block comments in their respective lines
	offset = 0
	for comment in docBlocks:
		lines.insert(comment.line - 1 + offset, comment.comment)
		offset = offset + 1

	return "".join(["%s" % (s) for s in lines]);

def usage():
	print("Usage: autocmt.py [-o] sourcefile")

def main():
	from clang.cindex import Index, Config
	from io import open

	# TODO: Don't hard code the clang library path
	Config.set_library_path("/usr/lib/llvm-3.3/lib")

	if len(sys.argv) == 1 or len(sys.argv) > 3:
		usage()
		sys.exit(1)

	cppFile = str()
	overwrite = False
	
	if "-o" in sys.argv:
		overwrite = True

	cppFile = sys.argv[len(sys.argv) - 1]
	
	index = Index.create()
	transUnit = index.parse(cppFile)
	docBlocks = get_doc_comments(transUnit.cursor, cppFile)
	source = source_with_doc_blocks(cppFile, docBlocks)
	if overwrite:
		with open(cppFile, "w") as file:
			file.write(unicode(source))
	else:
		sys.stdout.write(unicode(source))

if __name__ == '__main__':
	main()