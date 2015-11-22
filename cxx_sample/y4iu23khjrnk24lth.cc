#include <iostream>
#include <string>
#include <unistd.h>

int main() {
   std::string s;
   std::cin >> s;
   usleep(900000);
   std::cout << s;
   return 0;
}
