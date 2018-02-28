from geniusalt.models import Node, Instance, Module, IncludeRelationship
from .common import Operator

class RelationOperator(Operator):
    fields_defination = {'nodes': {'value_type' : list,
                                  'item_type': 'object_name_list',
                                  'item_model': Node},

                         'instances': {'value_type' : list,
                                      'item_type': 'object_name_list',
                                      'item_model': Instance},

                         'bind_modules': {'value_type': list,
                                             'item_type': 'object_name_list',
                                             'item_model': Module},

                         'bind_instances': {'value_type': list,
                                             'item_type': 'object_name_list',
                                             'item_model': Instance},

                         'included_instances': {'value_type': list,
                                             'item_type': 'object_name_list',
                                             'item_model': Instance},

                        }
    def bind(self):
        """
        To bind Module or pillar of Instance to a Node. Only bind in DB, not really to install objects for a real host.
        """
        fields_required, fields_optional = ['nodes'], ['bind_modules', 'bind_instances']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To get objects.
        bind_modules, bind_instances = [], []
        if validate_result.get('bind_modules'):
            bind_modules = validate_result['bind_modules']
        if validate_result.get('bind_instances'):
            bind_instances = validate_result['bind_instances']
            for i_obj in bind_instances:
                if i_obj.module_belong not in bind_modules:
                    bind_modules.append(i_obj.module_belong)
        if not (bind_modules or bind_instances):
            return "ERROR: 'bind_modules' or 'bind_instances' is required."

        ### To set nodes.
        for n_obj in validate_result['nodes']:
            if bind_modules:
                n_obj.bind_modules.add(*bind_modules)
            if bind_instances:
                n_obj.bind_instances.add(*bind_instances)

            n_obj.save()

        self.operator_return['message'] = "To Bind objects %s to Nodes %s succeed.\n" % (str([o.name for o in bind_modules + bind_instances]), str(self.parameters['nodes']))
        return self.operator_return

    def unbind(self):
        """
        To unbind Module or pillar of Instance from a Node.
        """
        fields_required, fields_optional = ['nodes'], ['bind_modules', 'bind_instances']

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To get objects.
        bind_modules = []
        bind_instances = []
        if validate_result.get('bind_modules'):
            bind_modules = validate_result['bind_modules']
        if validate_result.get('bind_instances'):
            bind_instances = validate_result['bind_instances']
        if not (bind_modules or bind_instances):
            return "ERROR: 'bind_modules' or 'bind_instances' is required."

        ### To set nodes.
        for n_obj in validate_result['nodes']:
            if bind_modules:
                n_obj.bind_modules.remove(*bind_modules)
            if bind_instances:
                n_obj.bind_instances.remove(*bind_instances)

            n_obj.save()

        self.operator_return['message'] = "To Unbind objects %s from Nodes %s succeed\n" % (str([o.name for o in bind_modules + bind_instances]), str(self.parameters['nodes']))
        return self.operator_return

    def include(self):
        """
        To set Instance objects to include other Instance object.
        """
        fields_required, fields_optional = ['instances', 'included_instances'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check instances.
        for i_obj in validate_result['instances']:
            if i_obj in validate_result['included_instances']:
                return "ERROR: Instance obj '%s' cannot include itself" % i_obj.name

        ### To set relationship.
        for i_obj in validate_result['instances']:
            r_queryset =IncludeRelationship.objects.filter(r_instance=i_obj)
            if r_queryset.exists():
                r_obj = r_queryset.get(r_instance=i_obj)
            else:
                r_obj = IncludeRelationship(r_instance=i_obj)
                r_obj.save()

            for ii_obj in validate_result['included_instances']:
                r_obj.r_included.add(ii_obj)
            r_obj.save()

        self.operator_return['message'] = "To set instances %s to include other instances %s succeed\n" % (str(self.parameters['instances']), str(self.parameters['included_instances']))
        return self.operator_return

    def exclude(self):
        """
        To set Instance objects to exclude other Instance object.
        """
        fields_required, fields_optional = ['instances', 'included_instances'], []

        ### To validate data in self.parameters.
        validate_result = self.dataValidating(fields_required, fields_optional)
        if not isinstance(validate_result, dict):
            return validate_result

        ### To check instances.
        for i_obj in validate_result['instances']:
            if i_obj in validate_result['included_instances']:
                return "ERROR: Instance obj '%s' cannot exclude itself" % i_obj.name

        ### To set nodes.
        for i_obj in validate_result['instances']:
            r_queryset =IncludeRelationship.objects.filter(r_instance=i_obj)
            if r_queryset.exists():
                r_obj = r_queryset.get(r_instance=i_obj)
                for ii_obj in validate_result['included_instances']:
                    r_obj.r_included.remove(ii_obj)
                r_obj.save()

        self.operator_return['message'] = "To set instances %s to exclude other instances %s succeed\n" % (str(self.parameters['instances']), str(self.parameters['included_instances']))
        return self.operator_return
