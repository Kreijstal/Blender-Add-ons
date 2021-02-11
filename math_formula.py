

import bpy


bl_info = {
    "name": "Node Math Formula",
    "author": "Wannes Malfait",
    "version": (0, 1, 0),
    "location": "Node Editor Toolbar",
    "description": "Quickly add math nodes by typing in a formula",
    "category": "Node",
    "blender": (2, 91, 0),  # Required so the add-on will actually load
}

# Operations used by the math node
math_operations = [
    # First element contains aliases for the function name
    # Second element is the actual function name
    # Third element is the number of arguments
    (('+', 'add'), 'ADD', 2),
    (('-', 'sub'), 'SUBTRACT', 2),
    (('*', 'mult'), 'MULTIPLY', 2),
    (('/', 'div'), 'DIVIDE', 2),
    (('*+', 'mult_add'), 'MULTIPLY_ADD', 3),
    (('sin', 'sine'), 'SINE', 1),
    (('cos', 'cosine'), 'COSINE', 1),
    (('tan', 'tangent'), 'TANGENT', 1),
    (('asin', 'arcsin', 'arcsine'), 'ARCSINE', 1),
    (('acos', 'arccos', 'arccosine'), 'ARCCOSINE', 1),
    (('atan', 'arctan', 'arctangent'), 'ARCTANGENT', 1),
    (('atan2', 'arctan2'), 'ARCTAN2', 2),
    (('sinh'), 'SINH', 1),
    (('cosh'), 'COSH', 1),
    (('tanh'), 'TANH', 1),
    (('^', 'pow', 'power'), 'POWER', 2),
    (('log', 'logarithm'), 'LOGARITHM', 2),
    (('sqrt'), 'SQRT', 1),
    (('1/sqrt', 'inv_sqrt'), 'INVERSE_SQRT', 1),
    (('e^x', 'e^', 'exp'), 'EXPONENT', 1),
    (('min', 'minimum'), 'MINIMUM', 2),
    (('max', 'maximum'), 'MAXIMUM', 2),
    (('<', 'less_than'), 'LESS_THAN', 2),
    (('>', 'greater_than'), 'GREATER_THAN', 2),
    (('sgn', 'sign'), 'SIGN', 1),
    (('==', 'compare'), 'COMPARE', 3),
    (('smin', 'smooth_min', 'smooth_minimum'), 'SMOOTH_MIN', 3),
    (('smax', 'smooth_max', 'smooth_maximum'), 'SMOOTH_MAX', 3),
    (('fract'), 'FRACT', 1),
    (('%', 'mod'), 'MODULO', 2),
    (('snap'), 'SNAP', 2),
    (('wrap'), 'WRAP', 3),
    (('pingpong', 'ping_pong'), 'PINGPONG', 2),
    (('abs', 'absolute'), 'ABSOLUTE', 1),
    (('round'), 'ROUND', 1),
    (('floor'), 'FLOOR', 1),
    (('ceil'), 'CEIL', 1),
    (('trunc', 'truncate'), 'TRUNCATE', 1),
    (('rad', 'to_rad', 'to_radians', 'radians'), 'RADIANS', 1),
    (('deg', 'to_deg', 'to_degrees', 'degrees'), 'DEGREES', 1)
]

vector_math_operations = [
    (('v+', 'vadd'), 'ADD', 2),
    (('v-', 'vsub'), 'SUBTRACT', 2),
    (('v*', 'vmult'), 'MULTIPLY', 2),
    (('v/', 'vdiv'), 'DIVIDE', 2),
    (('cross', 'cross_product'), 'CROSS_PRODUCT', 2),
    (('project'), 'PROJECT', 2),
    (('reflect'), 'REFLECT', 2),
    (('vsnap'), 'SNAP', 2),
    (('v%', 'mod'), 'MODULO', 2),
    (('vmin', 'vminimum'), 'MINIMUM', 2),
    (('vmax', 'vmaximum'), 'MAXIMUM', 2),
    (('dot', 'dot_product'), 'DOT_PRODUCT', 2),
    (('dist', 'distance'), 'DISTANCE', 2),
    (('length'), 'LENGTH', 1),
    (('scale'), 'SCALE', 2),
    (('normalize'), 'NORMALIZE', 1),
    (('vfloor'), 'FLOOR', 1),
    (('vceil'), 'CEIL', 1),
    (('vfract'), 'FRACT', 1),
    (('vabs', 'vabsolute'), 'ABSOLUTE', 1),
    (('vsin', 'vsine'), 'SINE', 1),
    (('vcos', 'vcosine'), 'COSINE', 1),
    (('vtan', 'vtangent'), 'TANGENT', 1),
    (('vwrap'), 'WRAP', 3),
]


class MF_Settings(bpy.types.PropertyGroup):
    formula: bpy.props.StringProperty(
        name="Formula",
        description="Formula written in Reverse Polish Notation",
        default="4 5 *",
    )
    temp_attr_name: bpy.props.StringProperty(
        name="Temporary Attribute",
        description="Name of the temporary attribute used to store in between results",
        default="mf_temp",
    )
    add_frame: bpy.props.BoolProperty(
        name="Add Frame",
        description='Put all the nodes in a frame',
        default=True,
    )


def mf_check(context):
    space = context.space_data
    return space.type == 'NODE_EDITOR' and space.node_tree is not None and space.tree_type == 'GeometryNodeTree'


class MFBase:
    @classmethod
    def poll(cls, context):
        return mf_check(context)


def is_float(str):
    try:
        float(str)
        return True
    except:
        return False


def parse_add(ind, str, vec, cls):
    if is_float(str):
        vec[ind] = float(str)
    else:
        cls.report(
            {'WARNING', f"Vectors are made up of floats separated by spaces. Got: {str}"})


def get_args(cls, stack, num_args, func_name):
    args = []
    for _ in range(num_args):
        if stack == []:
            cls.report(
                {'WARNING'}, f"Invalid number of arguments for {func_name.lower()}. Expected {num_args} arguments, got args: {args}.")
            args.append("no_arg")
        else:
            str = stack.pop()
            if str.endswith(")"):
                # It's a vector which we have to parse
                vec = [0, 0, 0]
                num = str
                if str == ")":
                    num = stack.pop()
                else:
                    # something like "20)""
                    num = str[:-1]
                parse_add(2, num, vec, cls)
                parse_add(1, stack.pop(), vec, cls)
                num = stack.pop()
                if num.startswith("("):
                    num = num[1:]
                else:
                    # Get rid of the left-over "("
                    stack.pop()
                parse_add(0, num, vec, cls)
                args.append(vec)
            elif is_float(str):
                args.append(float(str))
            else:
                # Check if it's a temporary attribute that we created
                if str.startswith(cls.temp_attr_name):
                    cls.number_of_temp_attributes -= 1
                args.append(str)
    args.reverse()
    return args


def place_node(tree, node, nodes):
    # First node
    if nodes == []:
        node.location = (0, 0)
    else:
        prev_node = nodes[-1]
        node.location = (prev_node.location.x +
                         prev_node.width + 50, prev_node.location.y)
        tree.links.new(prev_node.outputs["Geometry"], node.inputs["Geometry"])


def add_math_node(tree, nodes, args, func_name):
    node = tree.nodes.new(type="GeometryNodeAttributeMath")
    place_node(tree, node, nodes)
    node.operation = func_name
    l = len(args)
    # False -> ATTRIBUTE, True -> FLOAT
    arg_types = ['FLOAT' if type(
        arg) == float else 'ATTRIBUTE' for arg in args]
    # Convert the wrong vectors to strings
    for i in range(l):
        if type(args[i]) == list:
            # It's a vec3
            args[i] = str(args[i])
    # Possible types for the socket
    node.input_type_a = arg_types[0]
    if l >= 2:
        node.input_type_b = arg_types[1]
    if l == 3:
        node.input_type_c = arg_types[2]
    for i in range(l):
        # First input is Geometry so we skip it
        # The inputs are in the following order:
        # STRING, FLOAT for each socket
        # So we need to go in pairs of two
        offset = 0 if arg_types[i] == 'ATTRIBUTE' else 1
        node.inputs[1 + 2*i + offset].default_value = args[i]

    nodes.append(node)
    return node


def add_vector_math_node(tree, nodes, args, func_name):
    node = tree.nodes.new(type="GeometryNodeAttributeVectorMath")
    place_node(tree, node, nodes)
    node.operation = func_name
    l = len(args)
    # Socket ordering:
    # Geometry
    # A Attribute
    # A Vector
    # B Attribute
    # B Vector
    # B Float (Only used if func_name is 'SCALE')
    # C Attribute
    # C Vector
    # Result Attribute
    if func_name == 'SCALE':
        node.input_type_a = 'VECTOR'
        if type(args[0]) == float:
            args[0] = [args[0] for _ in range(3)]
            node.inputs[2].default_value = args[0]
        elif type(args[0]) == list:
            node.inputs[2].default_value = args[0]
        else:
            node.input_type_a = 'ATTRIBUTE'
            node.inputs[1].default_value = args[0]

        node.input_type_b = 'ATTRIBUTE'
        if type(args[1]) == float:
            node.input_type_b = 'FLOAT'
            node.inputs[5].default_value = args[1]
        elif type(args[1]) == list:
            node.inputs[3].default_value = str(args[1])
        else:
            node.inputs[3].default_value = args[1]
    else:
        # If it's a float we convert it to a vec3
        for i in range(l):
            print(args[i], type(args[i]))
            if type(args[i]) == float:
                args[i] = [args[i] for _ in range(3)]
            print(args[i], type(args[i]))
        node.input_type_a = 'ATTRIBUTE'
        entry = args[0]
        if type(entry) == list:
            node.input_type_a = 'VECTOR'
            node.inputs[2].default_value = entry
        else:
            node.inputs[1].default_value = entry
        if l >= 2:
            node.input_type_b = 'ATTRIBUTE'
            entry = args[1]
            if type(entry) == list:
                node.input_type_b = 'VECTOR'
                node.inputs[4].default_value = entry
            else:
                node.inputs[3].default_value = entry
        if l == 3:
            node.input_type_c = 'ATTRIBUTE'
            entry = args[2]
            if type(entry) == list:
                node.input_type_c = 'VECTOR'
                node.inputs[7].default_value = entry
            else:
                node.inputs[6].default_value = entry
    nodes.append(node)
    return node


class MF_OT_math_formula_add(bpy.types.Operator, MFBase):
    """Add the nodes for the formula"""
    bl_idname = "node.mf_math_formula_add"
    bl_label = "Add Math Formula"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Safe because of poll function
        tree = context.space_data.node_tree
        props = context.scene.math_formula_add
        # The formula that we parse. Should be in Reverse Polish Notation
        formula = props.formula
        # Used to store temporary results
        self.temp_attr_name = props.temp_attr_name
        # If two results are stored as temp attributes we need separate names
        self.number_of_temp_attributes = 0
        stack = []
        # The nodes that we added
        nodes = []
        # The brackets are only there for visual aid
        search_string = formula.replace('[', ' ').replace(
            ']', ' ').replace('{', ' ').replace('}', ' ').split(' ')
        for element in search_string:
            # In case of double spaces element might be ""
            if element.strip() == "":
                continue
            if element == "->":
                # Set the attribute name of the final result
                if nodes == []:
                    self.report(
                        {'WARNING', "No operations added but result set"})
                    return {'CANCELLED'}
                node = nodes[-1]
                result = search_string[-1]
                node.inputs["Result"].default_value = result
                break
            was_func = False
            func_name = None
            args = None
            for operation in math_operations:
                if element in operation[0]:
                    func_name = operation[1]
                    args = get_args(self, stack, operation[2], func_name)
                    was_func = True
                    break
            if was_func:
                node = add_math_node(tree, nodes, args, func_name)
                res_string = self.temp_attr_name + \
                    (str(self.number_of_temp_attributes)
                     if self.number_of_temp_attributes else "")
                node.inputs["Result"].default_value = res_string
                stack.append(res_string)
                self.number_of_temp_attributes += 1
            else:
                for operation in vector_math_operations:
                    if element in operation[0]:
                        func_name = operation[1]
                        args = get_args(self, stack, operation[2], func_name)
                        was_func = True
                        break
                if was_func:
                    node = add_vector_math_node(tree, nodes, args, func_name)
                    res_string = self.temp_attr_name + \
                        (str(self.number_of_temp_attributes)
                         if self.number_of_temp_attributes else "")
                    node.inputs["Result"].default_value = res_string
                    stack.append(res_string)
                    self.number_of_temp_attributes += 1
                else:  # It is an argument and not a function
                    stack.append(element)
        if props.add_frame and nodes != []:
            # Add all nodes in a frame
            frame = tree.nodes.new(type='NodeFrame')
            frame.label = formula
            for node in nodes:
                node.parent = frame
            frame.update()
        # Force an update
        tree.update_tag()
        return {'FINISHED'}


class VF_PT_panel(bpy.types.Panel, MFBase):
    bl_idname = "NODE_PT_mf_math_formula"
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Add Math Formula"
    bl_region_type = "UI"
    bl_category = "Math Formula"

    def draw(self, context):

        # Helper variables
        layout = self.layout
        scene = context.scene
        props = scene.math_formula_add

        col = layout.column(align=True)
        col.prop(props, 'formula')
        col.prop(props, 'temp_attr_name')
        col.prop(props, 'add_frame')
        col.separator()
        col.operator(MF_OT_math_formula_add.bl_idname)


classes = (
    MF_Settings,
    MF_OT_math_formula_add,
    VF_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.math_formula_add = bpy.props.PointerProperty(
        type=MF_Settings)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.math_formula_add


if __name__ == "__main__":
    register()
