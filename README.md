# Kubernetes Worker Demo

This repo provides an overview of the Prefect Kubernetes worker and how to use it. Some parts are specific to AWS, but the concepts should transfer to all major cloud providers.

## Resources

- [Introducing Prefect Workers and Projects](https://www.prefect.io/guide/blog/introducing-prefect-workers-and-projects/)
- [Worker Helm Chart](https://github.com/PrefectHQ/prefect-helm/tree/main/charts/prefect-worker#prefect-worker)
- [Projects Documentation](https://docs.prefect.io/latest/concepts/projects/)
- [Worker Pools Documentation](https://docs.prefect.io/latest/concepts/work-pools/)

## Create a cluster

Let's start by creating a new cluster. If you already have one, skip ahead to the next section. We'll use EKS backed by FARGATE,

```bash
eksctl create cluster --fargate --name kubernetes-worker
```

The process should take about 15 minutes and produce something like the following output,

```
2023-05-02 15:19:00 [ℹ]  eksctl version 0.124.0
2023-05-02 15:19:00 [ℹ]  using region us-east-2
2023-05-02 15:19:00 [ℹ]  setting availability zones to [us-east-2a us-east-2b us-east-2c]
2023-05-02 15:19:00 [ℹ]  subnets for us-east-2a - public:192.168.0.0/19 private:192.168.96.0/19
2023-05-02 15:19:00 [ℹ]  subnets for us-east-2b - public:192.168.32.0/19 private:192.168.128.0/19
2023-05-02 15:19:00 [ℹ]  subnets for us-east-2c - public:192.168.64.0/19 private:192.168.160.0/19
2023-05-02 15:19:00 [ℹ]  using Kubernetes version 1.23
2023-05-02 15:19:00 [ℹ]  creating EKS cluster "kubernetes-worker" in "us-east-2" region with Fargate profile
2023-05-02 15:19:00 [ℹ]  if you encounter any issues, check CloudFormation console or try 'eksctl utils describe-stacks --region=us-east-2 --cluster=kubernetes-worker'
2023-05-02 15:19:00 [ℹ]  Kubernetes API endpoint access will use default of {publicAccess=true, privateAccess=false} for cluster "kubernetes-worker" in "us-east-2"
2023-05-02 15:19:00 [ℹ]  CloudWatch logging will not be enabled for cluster "kubernetes-worker" in "us-east-2"
2023-05-02 15:19:00 [ℹ]  you can enable it with 'eksctl utils update-cluster-logging --enable-types={SPECIFY-YOUR-LOG-TYPES-HERE (e.g. all)} --region=us-east-2 --cluster=kubernetes-worker'
2023-05-02 15:19:00 [ℹ]
2 sequential tasks: { create cluster control plane "kubernetes-worker",
    2 sequential sub-tasks: {
        wait for control plane to become ready,
        create fargate profiles,
    }
}
2023-05-02 15:19:00 [ℹ]  building cluster stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:19:01 [ℹ]  deploying stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:19:31 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:20:01 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:21:01 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:22:01 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:23:02 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:24:02 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:25:02 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:26:02 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:27:02 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:28:03 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:29:03 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:30:03 [ℹ]  waiting for CloudFormation stack "eksctl-kubernetes-worker-cluster"
2023-05-02 15:32:04 [ℹ]  creating Fargate profile "fp-default" on EKS cluster "kubernetes-worker"
2023-05-02 15:34:15 [ℹ]  created Fargate profile "fp-default" on EKS cluster "kubernetes-worker"
2023-05-02 15:34:45 [ℹ]  "coredns" is now schedulable onto Fargate
2023-05-02 15:35:48 [ℹ]  "coredns" is now scheduled onto Fargate
2023-05-02 15:35:48 [ℹ]  "coredns" pods are now scheduled onto Fargate
2023-05-02 15:35:48 [ℹ]  waiting for the control plane to become ready
2023-05-02 15:35:49 [✔]  saved kubeconfig as "/Users/emilchristensen/.kube/config"
2023-05-02 15:35:49 [ℹ]  no tasks
2023-05-02 15:35:49 [✔]  all EKS cluster resources for "kubernetes-worker" have been created
2023-05-02 15:35:50 [ℹ]  kubectl command should work with "/Users/emilchristensen/.kube/config", try 'kubectl get nodes'
2023-05-02 15:35:50 [✔]  EKS cluster "kubernetes-worker" in "us-east-2" region is ready
```

## Create a service account

In order to authenticate with Prefect cloud, we'll want to use a service account. Create one with the Developer role in your workspace. Securely store the API key and set it as a Kubernetes secret,

```bash
kubectl create secret generic prefect-api-key --from-literal=key=<YOUR-KEY-HERE>
```

## Create a work pool

Next, go to the work pools page and create a new work pool with type `Kubernetes`. Set Finished Job TTL to 60 and Pod Watch Timeout Seconds to 300, but otherwise leave the defaults. We'll name our workpool `kubernetes`.

## Start a worker

Now we're ready to start a worker using the [Prefect Helm chart](https://github.com/prefecthq/prefect-helm#prefect-worker). Create a file called `values.yaml` and fill it in,

```yaml
worker:
  cloudApiConfig:
    accountId: "<YOUR-ACCOUNT-ID>"
    workspaceId: "<YOUR-WORKSPACE-ID>"
  config:
    workPool: "kubernetes"
```

Now we can install the worker,

```bash
helm repo add prefect https://prefecthq.github.io/prefect-helm/

helm repo update

helm install prefect-worker prefect/prefect-worker -f values.yaml
```

## Create an ECR repository

We'll want a remote image repository to store any custom images we build. If you already have a repository you want to use, skip this step. Here we'll use ECR, making sure to log in,

```bash
# Create a repo unless you already have one you wish to use
aws ecr create-repository --repository-name custom-flow-image

# Login to ECR
# Replace the region and account ID with your own values
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
```

## Create a variable

We could hardcode the image name our `prefect.yaml` file, but for the sake of demonstration and security, let's use a Prefect variable. Go to the variables page in the UI, set `Name` to `image_name`, and set `Value` to `$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/custom-flow-image` or equivalent.

## Deploy and run

At last we can deploy our flows and run them. The deploy command will actually build the images and push them to our remote repository.

```bash
prefect deploy --all --ci

prefect deployment run hello/default
prefect deployment run hello/arthur
prefect deployment run hello-parallel/default
```
