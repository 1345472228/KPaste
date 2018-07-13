# KPaste：一个简单的粘贴板

整体架构：
- web服务器： flask
- css框架： semantic ui
- 数据库： mysql
- orm： Sqlalchemy
- 数据库迁移： alembic

支持查看、新建、删除和编辑，以及一些简单的RESTful api因为是用来练手，所以精力大多都放在重构上了。

新增：有正确accesskey的用户，可以进行删除操作

暂时支持的api有:
- `/api/post/`
  - GET: 获取post列表。
  
    参数：page，perpage == 页数，每页文章数
  - POST：新建post。
  
    参数： title, author, language_id, validity_days, rawcontent, other, access_key

- `/api/post/<int:post_id>`
    - GET：获取一个post。
    
    - PUT：更新post。
    
      参数：access_key
    
    - DELETE：删除post。
    
      参数：access_key
    
 api返回的都是json。若成功，json对象中有键值对`{'succeed': true}`；若失败，有键值对`{'success': false, 'error': { 'message': <error_msg>, 'code': <error_code> }`
 
验证方式支持cookie方式和json字段提供Key两种方式
