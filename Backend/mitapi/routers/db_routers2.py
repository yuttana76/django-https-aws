from middleware import current_user

class multiDB_byLink:

    def db_for_read(self, model, user_id=None, **hints):
        compCode = current_user.get_compCode()
        if 'mpam' == compCode:
            return "mpam_db"
        elif 'mps' == compCode:
            return "mps_db"
    
        return "default"      

    def db_for_write(self, model, user_id=None, **hints):
        compCode = current_user.get_compCode()
        if 'mpam' == compCode:
            return "mpam_db"
        elif 'mps' == compCode:
            return "mps_db"
    
        return "default"  

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        compCode = current_user.get_compCode()
        if 'mpam' == compCode:
            return "mpam_db"
        elif 'mps' == compCode:
            return "mps_db"
    
        return "default"  
