# mysql-tunnel
mysql connector that can work via ssh tunnels if necessary

If using a ssh tunnel there will need to be a private ssh key for the current account.

All paramters for setting up ssh and mysql connections can be loaded from environmtal variables. If an ```.env``` file is being used for these settings and has not been loaded into the environment then it is expceted that ```python-dotenv``` will already have been used to read in the ```.env`` file. A sample file ```env.sample``` has been provided.

# Example Usage
from mysql_tunnel import TunnelSQL
```
with TunnelSQL(silent=False) as db
    sql = 'SELECT * FROM sample'
    results = db.execute(sql)
    print('Number of results: {}'.format(len(results))
    
    sql = 'SELECT * FROM sample WHERE id = %s'
    results = db.execute(sql, (7, ))
    print('Number of results: {}'.format(len(results))
```

By default the cursor returns each row as a list. To retreive each row as a dictionary pass ```cursor='DictCursor'```.
