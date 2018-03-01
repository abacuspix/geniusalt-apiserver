# geniusalt-apiserver


说明
========

对saltstack的二次封装，主要用于linux服务器集群环境下，对应用配置的集中管理。在这套apiserver的支持下，可以很方便的实现配置集中管理的web界面化。

对应的，我也在这套apiserver的基础上，写了一套linux命令行工具--'gnsalt'，参考项目：https://github.com/alan011/geniusalt-cli

在geniusalt中，将Linux服务器集群环境运行的后台服务抽象为一个个“应用实例（Instance）”。每个应用有它自己的中间件环境，比如有依赖tomcat的，有依赖weblogic的，有纯java自启动的服务，有依赖python环境的等等。这些中间件环境，我们将其抽象为一个个“模块(Module)”。而应用服务运行所在的服务器，我们将其抽象为“节点(Node)”。'实例（Instance）','模块（Module）','节点（Node）'是geniusalt中的三个基本数据对象。

针对每个模块，我们需要saltstack的file_root中，建立一个文件夹，文件夹中定义这个模块需要安装哪些软件包，创建哪些目录，启动哪些服务，配置哪些全局的配置文件等，并创建一个子目录'instance'（如果一个模块没有实例，则不用）。在instance目录中，定义每个应用实例（应用程序包）的安装目录，日志路径，配置文件，启动服务等等。最后，还需要为实例创建一个配置文件，'pillar.json'，用以定义这个模块的实例需要传入哪些pillar变量。

于数据层面而言，模块对象，即是saltstack的file_root下的一个目录以及一些列'.sls'文件，数据库中会记录模块的名称，以及此模块的实例所需要的pillar变量的定义；实例对象，即一组pillar变量键值对儿，在数据库中当然也会记录它从属于哪个模块；节点对象，会记录自己绑定了哪些模块，哪些实例。

配置的下发推送方式，分两种：一种是不明确指定配置对象（模块或者实例）的方式，一种是明确指定配置对象的方式。不明确的推送方式，需要我们先将配置对象绑定到某个节点，然后push这个节点，即可将这个节点上所有绑定的配置对象，应用到服务器；明确指定配置对象的方式，要求我们在调用push接口时，提供要推送的配置对象，push执行过程中，将仅推送明确指定的配置对象，而会忽略这个节点上已绑定的其他配置对象。当然，明确指定推送会自动记录节点对配置对象的绑定关系。

从我之前的单位使用情况来看，绝大多数情况下都是使用明确指定配置对象的推送方式，这样可以最大限度的降低本次变更对同一台服务器下运行的其他不相关应用的影响。


安装
========

geniusalt-apiserver用python3编写，在Django环境下运行。是一个相对独立的Django应用。



接口说明
========
