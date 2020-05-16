from flask_table import Table, Col


class Detail(Table):
    def sort_url(self, col_id, reverse=False):
        pass

    id = Col('id')
    distribution_file = Col('distribution_file')
    description = Col('description')


class Parameter(Table):
    def sort_url(self, col_id, reverse=False):
        pass

    id = Col('id')
    admin = Col('admin')
    is_pace = Col('is_pace')
    detail_id = Col('detail_id', show=False)
    created_on = Col('created_on')
    ongoing = Col('ongoing')


