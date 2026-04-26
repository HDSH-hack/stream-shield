import { cn } from "@/lib/cn";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description?: string;
  status?: string;
  className?: string;
};

export const PageHeader = ({
  eyebrow,
  title,
  description,
  status,
  className,
}: PageHeaderProps) => {
  return (
    <div
      className={cn(
        "mb-8 flex flex-col gap-5 md:flex-row md:items-start md:justify-between",
        className,
      )}
    >
      <div>
        <p className="text-sm font-medium text-shield-cyan">{eyebrow}</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-bold tracking-tight text-white md:text-5xl">
          {title}
        </h1>
        {description ? (
          <p className="mt-4 max-w-2xl text-base leading-7 text-shield-muted">
            {description}
          </p>
        ) : null}
      </div>
      {status ? (
        <div className="inline-flex w-fit rounded-full border border-shield-safe/20 bg-shield-safe/10 px-3 py-1.5 text-xs font-medium text-shield-safe">
          {status}
        </div>
      ) : null}
    </div>
  );
};
