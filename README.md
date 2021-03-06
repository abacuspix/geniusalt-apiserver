设计说明
------

geniusalt是对saltstack的二次封装，主要用于linux服务器集群环境下，对应用运行环境配置的集中管理。

geniusalt将沿用saltstack的sls文件编写规范，但，pillar不再写成文件，而是存入数据库中，在执行配置推送的时候才回传给saltstack。这样，可以很方便的实现配置集中管理的web界面化。

对应的，写了一套linux命令行工具--'gnsalt'，用以简化命令行的输入，美化展示数据（相比于单纯用curl调用API而言）。参考项目：https://github.com/alan011/geniusalt-cli

在geniusalt中，有三个基本的数据对象：
* 实例（instance）

    将Linux服务器集群环境中运行的后台应用服务，抽象为一个个应用实例。

* 模块（module）

    每个应用有它自己的中间件环境，比如有依赖tomcat的，有依赖weblogic的，有纯java自启动的服务，有依赖python环境的等等。这些中间件环境，我们将其抽象为一个个“模块(Module)”。

* 节点（node）

    而应用服务运行所在的服务器，我们将其抽象为“节点(Node)”。

针对每个模块，我们需要在saltstack的file_root中，以模块名称建立一个目录，目录下通过编写saltstack的sls文件来定义这个模块需要安装哪些软件包，创建哪些目录，启动哪些服务，配置哪些全局配置文件等，并创建一个子目录'instance'（如果一个模块没有实例，则不用）。在instance目录中，定义每个应用实例（应用程序包）的安装目录，日志路径，配置文件，启动服务等等。最后，还需要在模块目录下为实例创建一个配置文件，'pillar.json'，用以定义这个模块的实例需要传入哪些pillar变量。

于数据层面而言，模块对象，即是saltstack的file_root下的一个目录以及一些列'.sls'文件，数据库中会记录模块的名称，以及此模块的实例所需要的pillar变量的定义；实例对象，即一组pillar变量键值对儿，在数据库中当然也会记录它从属于哪个模块；节点对象，会记录自己绑定了哪些模块，哪些实例。

配置的下发推送方式，分两种：
* 推送时不明确指定配置对象（模块或者实例）

    这种方式，需要我们先将配置对象绑定到某个节点，然后push这个节点，即可将这个节点上所有绑定的配置对象，应用到服务器。

* 推送时明确指定配置对象

    这种方式，要求我们在调用push接口时，提供要推送的配置对象，push执行过程中，将仅推送明确指定的配置对象，而会忽略这个节点上已绑定的其他配置对象。当然，这会自动记录节点对配置对象的绑定关系。

从我目前的单位使用情况来看，绝大多数情况下都是使用明确指定配置对象的推送方式，这样可以最大限度的降低本次变更对同一台服务器下运行的其他不相关应用的影响。

最后，关于开发测试、集成测试、准生产、生产等“环境”的区分，我这是这样考虑的：

* 一个节点（即一台服务器）属于某一个环境

* 模块层不区分环境

    模块层所管理的是通用的共性的配置，比如安装什么软件包，创建哪些目录，管理通用配置文件等。

* 环境会在实例层面得以区分

    没有明确指定环境的pillar变量，作为实例默认pillar。比如，设置某tomcat实例xms默认大小为512m；

    针对具体的环境，可以设置本环境需要的pillar，比如，在生产环境中，设置这个实例xms大小设置为1024m;

    当推送这个实例到某个节点时，如果节点不是生产环境的则会使用默认的512m（如无其他环境配置），如果节点是生产环境的节点，则会使用1024m的配置。


安装
------

geniusalt-apiserver用python3编写，在Django环境下运行，是一个相对独立的Django应用。

* 依赖系统环境
    * OS: Linux各发行版本即可，不支持windows
    * python3
    * saltstack： 需要预先安装salt-master，安装方法请参考salt官网：https://repo.saltstack.com/#rhel

* 依赖python3软件包（pip安装即可）
    * django: 开发、测试都是用django-1.11
    * jsonfield

* 安装geniusalt-apiserver

    下载源码包，将所有文件放在一个目录下，作为一个django的app放在django的工程目录即可，注意配置settings.py以及导入url，
    ```
    url路径：./api/urls.py
    ```

* 启动服务
进入django的工程目录，执行以下命令

```
~$ cd /path/to/your/django_project/
~$ nohup python3 ./manage.py runserver 0.0.0.0:10080 &
```

功能与接口说明
------

* 接口URL（此处以本地调用为例）：

```
http://localhost:10080/geniusalt/api/v1/ingress
```

* 调用方式：只能用POST方法

* POST data参数说明
    * data段， 应该传一个json格式的字典。
    * 三个必填参数: 'auth_token', 'action', 'object'

'auto_token'用于接口调用的认证。目前版本，还没有做详细的权限划分，只要token认证通过，就能调用apiserver进行所有操作。
token的管理，请参考后文的token_manager使用方法。
```
'auth_token':'dLqsTdRa.1Mk17F2smGvvWJwHJgmffiLyPw4iruh6Dtt6ROnwoLPVH68mlWIYynnoBae4L19Z' #<8位的用户名>.<64位的密文串>
```

'object'用以指定要操作的对象，支持以下value：
```
'module'    # 操作一个module对象，可以使用别名：'-m','mod'
'instance'  # 操作一个instance对象，可以使用别名：'-s','inst'
'node'      # 操作一个node对象，可以使用别名：'-n'
'relation'  # 表示一个关系操作,
'push'      # 表示一个push操作，即将配置对象应用到实际的服务器。
```

'action'表示要执行的具体操作，支持以下value：
```
'scan'            # 自动添加node或module, 对于module还可以自动更新pillar参数列表。
                  # 支持操作对象：module, node

'add'             # 手动添加节点，模块，或者实例
                  # 支持操作对象：node, module, instance

'delete'          # 删除node, module, instance. 可以使用别名: 'del'
                  # 支持操作对象：node, module, instance

'show'            # 获取对象信息。
                  # 支持操作对象：node, module, instance

'pillarSet'       # 设置instance的pillar属性的变量值。可以使用别名：'pset'
                  # 支持操作对象：instance

'pillarDel'       # 删除instance的pillar属性的变量。  可以使用别名：'pdel'
                  # 支持操作对象：instance

'environmentSet'  # 可设置node的environment属性。别名：'eset', 'envSet'
                  # 支持操作对象：node

'lock'            # 锁定一个节点，模块，或者实例
                  # 注意，对于module，是将其lock_count属性加1，其值可以大于1。非0即为锁定状态。
                  # 处于锁定状态的对象，不能被push到实际服务器。
                  # 支持操作对象：node, module, instance

'unlock'          # 解锁一个节点，模块，或者实例
                  # 注意，对于module的解锁，是将lock_count减1，不是直接解锁，当lock_count值为0时，才真正处于解锁状态。
                  # 支持操作对象：node, module, instance

'showBind'        # 用于查询一个instance或module被绑定到哪些node，将返回一个node列表。别名：'showb'
                  # 支持操作对象：module, instance

'include'         # 用于设置一个instance包含另外一个instance
                  # 支持操作对象：relation

'exclude'         # 解除一个instance对另外一个instance的包含关系
                  # 支持操作对象：relation

'bind'            # 将instance或module绑定到node
                  # 支持操作对象：relation

'unbind'          # 解除instance或module与node的绑定关系
                  # 支持操作对象：relation

'push'            # 推送配置对象module或instance到实际服务器
                  # 支持操作对象：push
```
