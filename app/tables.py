from flask_table import Table, Col


class Detail(Table):
    def sort_url(self, col_id, reverse=False):
        pass

    id = Col('id')
    is_pace = Col('is_pace')
    distribution_file = Col('distribution_file')
    description = Col('description')


class Parameter(Table):
    def sort_url(self, col_id, reverse=False):
        pass

    id = Col('id')
    admin = Col('admin')
    detail_id = Col('detail_id', show=False)
    created_on = Col('created_on')
    on_going = Col('ongoing')


