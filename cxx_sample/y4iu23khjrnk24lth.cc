#include <iostream>
#include <string>
#include <unistd.h>

#include "foo.h"

int main() {
   std::string s;
   std::cin >> s;
   usleep(900000);
   std::cout << f(stoi(s));
   return 0;
}
