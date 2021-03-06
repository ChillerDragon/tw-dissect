import sys

GlobalIdCounter = 0
def GetID():
	global GlobalIdCounter
	GlobalIdCounter += 1
	return GlobalIdCounter
def GetUID():
	return "x%d"%GetID()

def FixCasing(Str):
	NewStr = ""
	NextUpperCase = True
	for c in Str:
		if NextUpperCase:
			NextUpperCase = False
			NewStr += c.upper()
		else:
			if c == "_":
				NextUpperCase = True
			else:
				NewStr += c.lower()
	return NewStr

def FormatName(type, name):
	if "*" in type:
		return "m_p" + FixCasing(name)
	if "[]" in type:
		return "m_a" + FixCasing(name)
	return "m_" + FixCasing(name)

class BaseType:
	def __init__(self, type_name):
		self._type_name = type_name
		self._target_name = "INVALID"
		self._id = GetID() # this is used to remember what order the members have in structures etc

	def Identifyer(self): return "x"+str(self._id)
	def TargetName(self): return self._target_name
	def TypeName(self): return self._type_name
	def ID(self): return self._id;

	def EmitDeclaration(self, name):
		return ["%s %s;"%(self.TypeName(), FormatName(self.TypeName(), name))]
	def EmitPreDefinition(self, target_name):
		self._target_name = target_name
		return []
	def EmitDefinition(self, name):
		return []

class MemberType:
	def __init__(self, name, var):
		self.name = name
		self.var = var

class Struct(BaseType):
	def __init__(self, type_name):
		BaseType.__init__(self, type_name)
	def Members(self):
		def sorter(a):
			return a.var.ID()
		m = []
		for name in self.__dict__:
			if name[0] == "_":
				continue
			m += [MemberType(name, self.__dict__[name])]
		try:
			m.sort(key = sorter)
		except:
			for v in m:
				print(v.name, v.var)
			sys.exit(-1)
		return m

	def EmitTypeDeclaration(self, name):
		lines = []
		lines += ["struct " + self.TypeName()]
		lines += ["{"]
		for member in self.Members():
			lines += ["\t"+l for l in member.var.EmitDeclaration(member.name)]
		lines += ["};"]
		return lines

	def EmitPreDefinition(self, target_name):
		BaseType.EmitPreDefinition(self, target_name)
		lines = []
		for member in self.Members():
			lines += member.var.EmitPreDefinition(target_name+"."+member.name)
		return lines
	def EmitDefinition(self, name):
		lines = ["/* %s */ {" % self.TargetName()]
		for member in self.Members():
			lines += ["\t" + " ".join(member.var.EmitDefinition("")) + ","]
		lines += ["}"]
		return lines

class Array(BaseType):
	def __init__(self, type):
		BaseType.__init__(self, type.TypeName())
		self.type = type
		self.items = []
	def Add(self, instance):
		if instance.TypeName() != self.type.TypeName():
			error("bah")
		self.items += [instance]
	def EmitDeclaration(self, name):
		return ["int m_Num%s;"%(FixCasing(name)),
			"%s *%s;"%(self.TypeName(), FormatName("[]", name))]
	def EmitPreDefinition(self, target_name):
		BaseType.EmitPreDefinition(self, target_name)

		lines = []
		i = 0
		for item in self.items:
			lines += item.EmitPreDefinition("%s[%d]"%(self.Identifyer(), i))
			i += 1

		if len(self.items):
			lines += ["static %s %s[] = {"%(self.TypeName(), self.Identifyer())]
			for item in self.items:
				itemlines = item.EmitDefinition("")
				lines += ["\t" + " ".join(itemlines).replace("\t", " ") + ","]
			lines += ["};"]
		else:
			lines += ["static %s *%s = 0;"%(self.TypeName(), self.Identifyer())]

		return lines
	def EmitDefinition(self, name):
		return [str(len(self.items))+","+self.Identifyer()]

# Basic Types

class Int(BaseType):
	def __init__(self, value):
		BaseType.__init__(self, "int")
		self.value = value
	def Set(self, value):
		self.value = value
	def EmitDefinition(self, name):
		return ["%d"%self.value]
		#return ["%d /* %s */"%(self.value, self._target_name)]

class Float(BaseType):
	def __init__(self, value):
		BaseType.__init__(self, "float")
		self.value = value
	def Set(self, value):
		self.value = value
	def EmitDefinition(self, name):
		return ["%ff"%self.value]
		#return ["%d /* %s */"%(self.value, self._target_name)]

class String(BaseType):
	def __init__(self, value):
		BaseType.__init__(self, "const char*")
		self.value = value
	def Set(self, value):
		self.value = value
	def EmitDefinition(self, name):
		return ['"'+self.value+'"']

class Pointer(BaseType):
	def __init__(self, type, target):
		BaseType.__init__(self, "%s*"%type().TypeName())
		self.target = target
	def Set(self, target):
		self.target = target
	def EmitDefinition(self, name):
		return ["&"+self.target.TargetName()]

class TextureHandle(BaseType):
	def __init__(self):
		BaseType.__init__(self, "IGraphics::CTextureHandle")
	def EmitDefinition(self, name):
		return ["IGraphics::CTextureHandle()"]

class SampleHandle(BaseType):
	def __init__(self):
		BaseType.__init__(self, "ISound::CSampleHandle")
	def EmitDefinition(self, name):
		return ["ISound::CSampleHandle()"]

# helper functions

def EmitTypeDeclaration(root):
	for l in root().EmitTypeDeclaration(""):
		print(l)

def EmitDefinition(root, name):
	for l in root.EmitPreDefinition(name):
		print(l)
	print("%s %s = " % (root.TypeName(), name))
	for l in root.EmitDefinition(name):
		print(l)
	print(";")

# Network stuff after this

class Object:
	pass

class Enum:
	def __init__(self, name, values):
		self.name = name
		self.values = values

class Flags:
	def __init__(self, name, values):
		self.name = name
		self.values = values

class NetObject:
	def __init__(self, name, variables):
		l = name.split(":")
		self.name = l[0]
		self.base = ""
		if len(l) > 1:
			self.base = l[1]
		self.base_struct_name = "CNetObj_%s" % self.base
		self.struct_name = "CNetObj_%s" % self.name
		self.enum_name = "NETOBJTYPE_%s" % self.name.upper()
		self.variables = variables
	def emit_declaration(self):
		if self.base:
			lines = ["struct %s : public %s"%(self.struct_name,self.base_struct_name), "{"]
		else:
			lines = ["struct %s"%self.struct_name, "{"]
		for v in self.variables:
			lines += ["\t"+line for line in v.emit_declaration()]
		lines += ["};"]
		return lines
	def emit_validate(self):
		lines = ["case %s:" % self.enum_name]
		lines += ["{"]
		lines += ["\t%s *pObj = (%s *)pData;"%(self.struct_name, self.struct_name)]
		lines += ["\tif(sizeof(*pObj) != Size) return -1;"]
		for v in self.variables:
			lines += ["\t"+line for line in v.emit_validate()]
		lines += ["\treturn 0;"]
		lines += ["}"]
		return lines


class NetEvent(NetObject):
	def __init__(self, name, variables):
		NetObject.__init__(self, name, variables)
		self.base_struct_name = "CNetEvent_%s" % self.base
		self.struct_name = "CNetEvent_%s" % self.name
		self.enum_name = "NETEVENTTYPE_%s" % self.name.upper()

class NetMessage(NetObject):
	def __init__(self, name, variables):
		NetObject.__init__(self, name, variables)
		self.enum_name = "NETMSGTYPE_%s" % self.name.upper()
	def emit_unpack(self):
		lines = []
		lines += ["[Const.%s] = function (data, offset, size)" % self.enum_name]
		lines += ["\tlocal tree = { name = '%s', start = offset, size = size }" % (self.name,)]
		lines += ["\tlocal msg_pos = offset"]
		for v in self.variables:
			lines += ["\t"+line for line in v.emit_unpack()]
		# for v in self.variables:
		# 	lines += ["\t"+line for line in v.emit_unpack_check()]
		lines += ["\treturn tree"]
		lines += ["end,"]
		return lines

class NetSys(NetObject):
	def __init__(self, name, variables):
		NetObject.__init__(self, name, variables)
		self.enum_name = "NETMSG_%s" % self.name.upper()
	def emit_unpack(self):
		lines = []
		lines += ["[Const.%s] = function (data, offset, size)" % self.enum_name]
		lines += ["\tlocal tree = { name = '%s', start = offset, size = size }" % (self.name,)]
		lines += ["\tlocal msg_pos = offset"]
		for v in self.variables:
			lines += ["\t"+line for line in v.emit_unpack()]
		# for v in self.variables:
		# 	lines += ["\t"+line for line in v.emit_unpack_check()]
		lines += ["\treturn tree"]
		lines += ["end,"]
		return lines

class NetVariable:
	def __init__(self, name):
		self.name = name
	def emit_validate(self):
		return []
	def emit_unpack(self):
		return []
	def emit_unpack_check(self):
		return []

class NetString(NetVariable):
	def emit_unpack(self):
		lines = []
		lines += ['local value, next_pos = Struct.unpack("s", data, msg_pos+1)']
		lines += ['table.insert(tree, { name = "%s", start = msg_pos, size = next_pos - msg_pos - 1, value = value })' % (self.name)]
		lines += ['msg_pos = next_pos-1']
		return lines

class NetRawString(NetVariable):
	def __init__(self, name, size):
		NetVariable.__init__(self, name)
		self.size = size
	def emit_unpack(self):
		lines = []
		lines += ['local value = data:sub(msg_pos+1, msg_pos+%d)' % self.size]
		lines += ['table.insert(tree, { name = "%s", start = msg_pos, size = %d, value = value })' % (self.name, self.size)]
		lines += ['msg_pos = msg_pos + %d' % self.size]
		return lines

class NetHex(NetVariable):
	def __init__(self, name, size):
		NetVariable.__init__(self, name)
		self.size = size
	def emit_unpack(self):
		lines = []
		lines += ['local value = data:sub(msg_pos+1, msg_pos+%d)' % self.size]
		lines += ['table.insert(tree, { name = "%s", start = msg_pos, size = %d, value = (value):tohex() })' % (self.name, self.size)]
		lines += ['msg_pos = msg_pos + %d' % self.size]
		return lines

class NetStringStrict(NetVariable):
	# dont do sanitize
	def emit_unpack(self):
		lines = []
		lines += ['local value, next_pos = Struct.unpack("s", data, msg_pos+1)']
		lines += ['table.insert(tree, { name = "%s", start = msg_pos, size = next_pos - msg_pos - 1, value = value })' % (self.name)]
		lines += ['msg_pos = next_pos-1']
		return lines

class NetIntAny(NetVariable):
	def emit_unpack(self):
		lines = []
		lines += ['local value, length = unpack_int(data, msg_pos+1)']
		lines += ['table.insert(tree, { name = "%s", start = msg_pos, size = length, value = value })' % (self.name)]
		lines += ['msg_pos = msg_pos + length']
		return lines

class NetIntRange(NetIntAny):
	def __init__(self, name, min, max):
		NetIntAny.__init__(self,name)
		self.min = str(min)
		self.max = str(max)
	def emit_validate(self):
		return ["if(!CheckInt(\"%s\", pObj->%s, %s, %s)) return -1;"%(self.name, self.name, self.min, self.max)]
	def emit_unpack_check(self):
		return ["if(!CheckInt(\"%s\", pMsg->%s, %s, %s)) break;"%(self.name, self.name, self.min, self.max)]

class NetEnum(NetIntRange):
	def __init__(self, name, enum):
		NetIntRange.__init__(self, name, 0, len(enum.values)-1)

class NetFlag(NetIntAny):
	def __init__(self, name, flag):
		NetIntAny.__init__(self, name)
		if len(flag.values) > 0:
			self.mask = "%s_%s" % (flag.name, flag.values[0])
			for i in flag.values[1:]:
				self.mask += "|%s_%s" % (flag.name, i)
		else:
			self.mask = "0"
	def emit_validate(self):
		return ["if(!CheckFlag(\"%s\", pObj->%s, %s)) return -1;"%(self.name, self.name, self.mask)]
	def emit_unpack_check(self):
		return ["if(!CheckFlag(\"%s\", pMsg->%s, %s)) break;"%(self.name, self.name, self.mask)]

class NetBool(NetIntRange):
	def __init__(self, name):
		NetIntRange.__init__(self,name,0,1)

class NetTick(NetIntRange):
	def __init__(self, name):
		NetIntRange.__init__(self,name,0,'max_int')

class NetArray(NetVariable):
	def __init__(self, var, size):
		self.base_name = var.name
		self.var = var
		self.size = size
		self.name = self.base_name + "[%d]"%self.size
	def emit_validate(self):
		lines = []
		for i in range(self.size):
			self.var.name = self.base_name + "[%d]"%i
			lines += self.var.emit_validate()
		return lines
	def emit_unpack(self):
		lines = []
		for i in range(self.size):
			self.var.name = self.base_name + "[%d]"%i
			lines += self.var.emit_unpack()
		return lines
	def emit_unpack_check(self):
		lines = []
		for i in range(self.size):
			self.var.name = self.base_name + "[%d]"%i
			lines += self.var.emit_unpack_check()
		return lines
