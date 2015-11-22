for i in range(100):
    t = open('t' + str(i) + '.test', 'w')
    t.write(str(i))
    a = open('a' + str(i) + '.test', 'w')
    a.write(str(i))
