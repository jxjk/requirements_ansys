# database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///requirements_analyst.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # 检查并添加projects表的creator字段（如果不存在）
        try:
            # 查询表结构
            result = db.session.execute(text("PRAGMA table_info(projects)"))
            columns = [row[1] for row in result.fetchall()]
            
            # 如果creator字段不存在，则添加它
            if 'creator' not in columns:
                db.session.execute(text("ALTER TABLE projects ADD COLUMN creator VARCHAR(100)"))
                db.session.commit()
                print("已添加projects.creator字段")
        except Exception as e:
            print(f"检查或添加creator字段时出错: {e}")
            db.session.rollback()
    
    return db