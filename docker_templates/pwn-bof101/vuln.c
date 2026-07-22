#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void win(void) {
    char buf[256];
    FILE *fp = fopen("/flag", "r");
    if (!fp) {
        puts("flag missing");
        return;
    }
    if (fgets(buf, sizeof(buf), fp)) {
        printf("Congrats! %s", buf);
        fflush(stdout);
    }
    fclose(fp);
}

void vuln(void) {
    char buf[64];
    puts("Buffer Overflow 101 — send your payload:");
    fflush(stdout);
    gets(buf);
    printf("You said: %s\n", buf);
    fflush(stdout);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    alarm(60);
    vuln();
    return 0;
}
