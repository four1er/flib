#pragma once
#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <future>
#include <stdexcept>


class ThreadPool {
    public:
        explicit ThreadPool(size_t num_of_threads = std::thread::hardware_concurrency());

        TreadPool(const ThreadPool&) = delete;
        ThreadPool& operator=(const ThreadPool&) = delete;

        ~ThreadPool();

        template<typename F, typename... Args>
        auto sumbit(F&&f, Args&&... args) -> std::future<decltype(f(args...))>;


    private:
        std::vector<std::thread> workers_;
        std::queue<std::function<void()>> tasks_;
        std::mutex mutex_;
        std::condition_variable condition_;
        bool stop_;
};

inline ThreadPool::ThreadPool(size_t num_of_threads) {
    for (size_t i = 0; i < num_of_threads; ++i) {
        workers_.emplace_back([this]{
            while(true){
                std::function<void()> task;
                {
                    std::unique_lock<std::mutex> lock(this->mutex_);
                    this->condition_.wait(lock, [this](){
                        return this->stop_ || !this->tasks_.empty();
                    });

                    if (this->stop_ && this->tasks_.empty()) {
                        return;
                    }

                    task=std::move(this->tasks_.front());
                    this->tasks_.pop();
                }
                task();
            }
        });
    }
}


inline ThreadPool::~ThreadPool() {
    {
        std::unique_lock<std::mutex> lock(mutex_);
        stop_ = true;
    }
    condition_.notify_all();
    for (std::thread &worker : workers_) {
        if (worker.joinable()) {
            worker.join();
        }
    }
}

template<typename F, typename... Args>
auto ThreadPool::sumbit(F&& f, Args&&... args) -> std::future<decltype(f(args...))> {
    using ReturnType = decltype(f(args...));
    auto task = std::make_shared<std::packaged_task<ReturnType()>>(
        std::bind(std::forward<F>(f), std::forward<Args>(args)...)
    );

    std::future<ReturnType> res = task->get_future();
    {
        std::unique_lock<std::mutex> lock(mutex_);
        if (stop_) {
            throw std::runtime_error("submit on stopped ThreadPool");
        }
        tasks_.emplace([task](){ (*task)(); });
    }
    condition_.notify_one();
    return res;
}


