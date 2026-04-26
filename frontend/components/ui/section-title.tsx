type SectionTitleProps = {
  title: string;
  description?: string;
};

export const SectionTitle = ({ title, description }: SectionTitleProps) => {
  return (
    <div className="mb-4">
      <h2 className="text-sm font-semibold text-white">{title}</h2>
      {description ? (
        <p className="mt-1 text-xs leading-5 text-shield-muted">{description}</p>
      ) : null}
    </div>
  );
};
