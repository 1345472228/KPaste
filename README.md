# KPaste：一个简单的粘贴板

整体架构：
- web服务器： flask
- css框架： semantic ui
- 数据库： mysql
- orm： Sqlalchemy
- 数据库迁移： alembic

暂时只支持查看和新建，以及一些简单的RESTful api因为是用来练手，所以精力大多都放在重构上了。

暂时支持的api有:
- `/api/post/`
  - GET: 获取post列表。
  
    参数：page，perpage == 页数，每页文章数
  - POST：新建post。
  
    参数： title, author, language_id, validity_days, rawcontent, other

- `/api/post/<int:post_id>`
    - GET：获取一个post。
    
    - PUT：更新post。
    
    - DELETE：删除post。
    
 api返回的都是json。若成功，json对象中有键值对`{'succeed': '1'}`；若失败，有键值对`{'error': <error info>}`
