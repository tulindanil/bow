for i in range(100):
    t = open('t' + str(i) + '.test', 'w')
    a = open('a' + str(i) + '.test', 'w')

    if i % 25 == 0:
        a.write(str(1))
    else:
        a.write(str(i))
    t.write(str(i))
