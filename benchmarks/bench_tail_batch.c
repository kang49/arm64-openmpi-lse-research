#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <pthread.h>
#include <sched.h>

#define BATCH_SIZE 32
#define BATCHES    20000

static volatile uint64_t __attribute__((aligned(128))) shared_64 = 0;
static pthread_barrier_t bar;
static double ns_per_tick = 0.0;

typedef struct {
    int tid;
    int mode; // 0 = LL/SC (ldaxr/stlxr), 1 = LSE (ldaddal)
    double *lat_ns;
    uint64_t retries;
} thread_arg_t;

static inline uint64_t read_cntvct(void) {
    uint64_t val;
    __asm__ __volatile__("isb\n\tmrs %0, cntvct_el0" : "=r"(val) :: "memory");
    return val;
}

static inline uint64_t read_cntfrq(void) {
    uint64_t val;
    __asm__ __volatile__("mrs %0, cntfrq_el0" : "=r"(val));
    return val;
}

static int cmp_dbl(const void *a, const void *b) {
    double da = *(const double *)a;
    double db = *(const double *)b;
    return (da > db) - (da < db);
}

void *worker(void *arg) {
    thread_arg_t *a = (thread_arg_t *)arg;
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(a->tid % 4, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);

    a->lat_ns = (double *)malloc(BATCHES * sizeof(double));
    uint64_t retries = 0;

    // Warmup
    for (int w = 0; w < 5000; w++) {
        __atomic_add_fetch(&shared_64, 1, __ATOMIC_RELAXED);
    }

    pthread_barrier_wait(&bar);

    if (a->mode == 0) {
        for (int b = 0; b < BATCHES; b++) {
            uint64_t t0 = read_cntvct();
            for (int k = 0; k < BATCH_SIZE; k++) {
                uint64_t oldv, newv;
                uint32_t status;
                do {
                    __asm__ __volatile__(
                        "ldaxr %0, [%3]\n"
                        "add   %1, %0, #1\n"
                        "stlxr %w2, %1, [%3]\n"
                        : "=&r"(oldv), "=&r"(newv), "=&r"(status)
                        : "r"(&shared_64)
                        : "memory");
                    if (status != 0) retries++;
                } while (status != 0);
            }
            uint64_t t1 = read_cntvct();
            a->lat_ns[b] = ((double)(t1 - t0) * ns_per_tick) / BATCH_SIZE;
        }
    } else {
        for (int b = 0; b < BATCHES; b++) {
            uint64_t t0 = read_cntvct();
            for (int k = 0; k < BATCH_SIZE; k++) {
                uint64_t oldv;
                __asm__ __volatile__(
                    "ldaddal %1, %0, [%2]\n"
                    : "=r"(oldv)
                    : "r"(1ULL), "r"(&shared_64)
                    : "memory");
            }
            uint64_t t1 = read_cntvct();
            a->lat_ns[b] = ((double)(t1 - t0) * ns_per_tick) / BATCH_SIZE;
        }
    }
    a->retries = retries;
    return NULL;
}

int main(void) {
    uint64_t freq = read_cntfrq();
    ns_per_tick = 1e9 / (double)freq;

    // Calibrate bare timer overhead
    uint64_t ov_sum = 0;
    for (int i = 0; i < 10000; i++) {
        uint64_t t0 = read_cntvct();
        uint64_t t1 = read_cntvct();
        ov_sum += (t1 - t0);
    }
    printf("Timer: cntfrq=%llu Hz (%.3f ns/tick), Back-to-back isb+mrs overhead: %.2f ns/batch (%.2f ns/op amortized)\n",
           (unsigned long long)freq, ns_per_tick,
           ((double)ov_sum / 10000.0) * ns_per_tick,
           (((double)ov_sum / 10000.0) * ns_per_tick) / BATCH_SIZE);

    const char *names[] = {"LL/SC (ldaxr/stlxr)", "LSE (ldaddal)"};
    for (int mode = 0; mode < 2; mode++) {
        for (int nth = 1; nth <= 4; nth++) {
            pthread_t th[4];
            thread_arg_t args[4];
            pthread_barrier_init(&bar, NULL, nth);
            shared_64 = 0;
            for (int t = 0; t < nth; t++) {
                args[t].tid = t;
                args[t].mode = mode;
                pthread_create(&th[t], NULL, worker, &args[t]);
            }
            size_t total = (size_t)nth * BATCHES;
            double *all_lat = (double *)malloc(total * sizeof(double));
            uint64_t sum_retries = 0;
            for (int t = 0; t < nth; t++) {
                pthread_join(th[t], NULL);
                for (int b = 0; b < BATCHES; b++) {
                    all_lat[(size_t)t * BATCHES + b] = args[t].lat_ns[b];
                }
                free(args[t].lat_ns);
                sum_retries += args[t].retries;
            }
            pthread_barrier_destroy(&bar);

            qsort(all_lat, total, sizeof(double), cmp_dbl);
            double sum = 0, sum2 = 0;
            for (size_t i = 0; i < total; i++) {
                sum += all_lat[i];
                sum2 += all_lat[i] * all_lat[i];
            }
            double mean = sum / total;
            double var = (sum2 / total) - (mean * mean);
            double p50 = all_lat[(size_t)(0.50 * total)];
            double p95 = all_lat[(size_t)(0.95 * total)];
            double p99 = all_lat[(size_t)(0.99 * total)];
            double p999 = all_lat[(size_t)(0.999 * total)];

            printf("%-20s | N=%d | Mean: %6.2f | Var: %7.2f | p50: %6.2f | p95: %6.2f | p99: %6.2f | p99.9: %7.2f | Aborts/op: %.3f\n",
                   names[mode], nth, mean, var, p50, p95, p99, p999,
                   (double)sum_retries / (total * BATCH_SIZE));
            free(all_lat);
        }
        printf("-----------------------------------------------------------------------------------------------------------------\n");
    }
    return 0;
}
