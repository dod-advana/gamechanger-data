class AutoRepr:
    """Simple, generic __repr__ for all class properties, sans those that start with underscores"""
    def __repr__(self):
        items = ("%s = %r" % (k, v) for k, v in self.__dict__.items() if not k.startswith('_'))
        return "<%s: {%s}>" % (self.__class__.__name__, ', '.join(items))