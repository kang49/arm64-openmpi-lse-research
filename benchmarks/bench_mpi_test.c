#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

#define POLLS 1000000

int main(int argc, char **argv) {
    int provided;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_MULTIPLE, &provided);

    int rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    char buf[64] = {0};
    MPI_Request req;
    int flag = 0;

    if (rank == 0) {
        MPI_Irecv(buf, 64, MPI_BYTE, 1, 0, MPI_COMM_WORLD, &req);
        // Warmup
        for (int i = 0; i < 10000; i++) {
            MPI_Test(&req, &flag, MPI_STATUS_IGNORE);
        }
        double t0 = MPI_Wtime();
        for (int i = 0; i < POLLS; i++) {
            MPI_Test(&req, &flag, MPI_STATUS_IGNORE);
        }
        double t1 = MPI_Wtime();
        printf("MPI_Test_ns_per_call: %.2f ns (total %.4f s for %d calls)\n",
               ((t1 - t0) * 1e9) / POLLS, t1 - t0, POLLS);
        MPI_Barrier(MPI_COMM_WORLD);
        MPI_Wait(&req, MPI_STATUS_IGNORE);
    } else {
        MPI_Barrier(MPI_COMM_WORLD);
        MPI_Send(buf, 64, MPI_BYTE, 0, 0, MPI_COMM_WORLD);
    }

    MPI_Finalize();
    return 0;
}
